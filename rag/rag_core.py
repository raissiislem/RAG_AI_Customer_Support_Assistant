"""
Core RAG logic: retrieval + prompt building + generation using Google Gemini.
Now with conversation history support — follow-up questions like
"go more in details" get rewritten into standalone questions before
retrieval, using the last few turns of the conversation.
"""
from dotenv import load_dotenv

load_dotenv()

import os

os.environ["HF_HUB_OFFLINE"] = "1"

from google import genai
from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer

COLLECTION_NAME = "biat_docs"
QDRANT_PORT = 6335

# Gemini model
GEMINI_MODEL = "gemini-2.5-flash"

TOP_K = 4
MIN_SCORE = 0.5
HISTORY_TURNS_USED = 3  # how many previous Q&A pairs to consider for context

SYSTEM_PROMPT = """
Tu es l'assistant virtuel officiel de la BIAT.

Tu réponds UNIQUEMENT à partir des informations fournies.

Règles strictes :
- N'utilise QUE les informations présentes dans les documents.
- N'invente jamais une réponse.
- Si les documents ne contiennent pas la réponse, réponds exactement :

"Je n'ai pas cette information dans les documents disponibles, merci de contacter votre agence BIAT ou le service client."

- Réponds en français.
- Sois clair, professionnel et concis.
- Ne fais jamais référence au "contexte" ou aux "documents" dans ta réponse.
"""

CONTEXTUALIZE_PROMPT = """Voici l'historique récent de la conversation entre un client et l'assistant BIAT :

{history}

Nouveau message du client : "{new_question}"

Ta tâche : reformule ce nouveau message en une question autonome et complète, \
compréhensible sans le reste de la conversation. Si le message fait référence \
à une réponse précédente (ex: "donne plus de détails", "et pour les cartes ?"), \
intègre ce sujet explicitement dans la question reformulée. Corrige aussi les \
fautes de frappe évidentes.

Si le nouveau message est déjà une question autonome et claire, renvoie-le tel quel.

Réponds UNIQUEMENT avec la question reformulée, sans aucune explication ni guillemets."""


class RAGEngine:
    """
    Loads Qdrant, embedding model and Gemini client once
    when the API starts.
    """

    def __init__(self):
        # Check API key
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError(
                "GEMINI_API_KEY environment variable is not set."
            )

        # Vector DB
        self.client = QdrantClient(
            host="localhost",
            port=QDRANT_PORT,
        )

        # Embedding model
        self.embed_model = SentenceTransformer("BAAI/bge-m3")

        # Gemini client
        self.gemini = genai.Client(api_key=api_key)

    def retrieve(self, query_text, top_k=TOP_K):
        query_vector = (
            self.embed_model.encode(
                query_text,
                normalize_embeddings=True,
            ).tolist()
        )

        response = self.client.query_points(
            collection_name=COLLECTION_NAME,
            query=query_vector,
            limit=top_k,
        )

        return response.points

    def contextualize_query(self, history: list[dict], new_question: str) -> str:
        """
        Rewrites a follow-up message into a standalone question using recent
        conversation history. Runs BEFORE retrieval, so vague follow-ups
        ("go more in details") get resolved into something embeddable
        ("donne plus de détails sur le CRÉDIMÉDIA Platinum").
        """
        if not history:
            return new_question  # first message in the session, nothing to resolve

        recent = history[-HISTORY_TURNS_USED:]
        history_text = "\n".join(
            f"Client: {turn['question']}\nAssistant: {turn['answer']}" for turn in recent
        )

        prompt = CONTEXTUALIZE_PROMPT.format(history=history_text, new_question=new_question)

        response = self.gemini.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt,
        )

        rewritten = response.text.strip().strip('"')
        return rewritten if rewritten else new_question

    def build_prompt(self, query_text, chunks):
        context_blocks = []

        for chunk in chunks:
            context_blocks.append(
                f"""Document : {chunk.payload['title']}

{chunk.payload['text']}"""
            )

        context = "\n\n-------------------------\n\n".join(context_blocks)

        return f"""
Informations BIAT :

{context}

Question du client :

{query_text}

Réponds uniquement à partir des informations ci-dessus.
"""

    def ask(self, query_text: str, history: list[dict] | None = None) -> dict:
        """
        Args:
            query_text: the user's raw new message
            history: list of {"question": str, "answer": str} from earlier
                     in this session, oldest first. Pass None or [] for the
                     first message of a conversation.

        Returns:
        {
            "answer": str,
            "sources": list[str],
            "matched": bool,
            "standalone_question": str  # what was actually searched — useful for debugging
        }
        """
        history = history or []

        # Step 1: resolve follow-ups / typos into a standalone question BEFORE retrieval
        standalone_question = self.contextualize_query(history, query_text)

        # Step 2: retrieve using the resolved question, not the raw message
        chunks = self.retrieve(standalone_question)

        relevant_chunks = [
            c for c in chunks
            if c.score >= MIN_SCORE
        ]

        if not relevant_chunks:
            return {
                "answer": (
                    "Je n'ai pas cette information dans les documents "
                    "disponibles, merci de contacter votre agence BIAT "
                    "ou le service client."
                ),
                "sources": [],
                "matched": False,
                "standalone_question": standalone_question,
            }

        prompt = self.build_prompt(
            standalone_question,
            relevant_chunks,
        )

        full_prompt = f"""
{SYSTEM_PROMPT}

{prompt}
"""

        response = self.gemini.models.generate_content(
            model=GEMINI_MODEL,
            contents=full_prompt,
        )

        answer = response.text.strip()

        sources = []

        for chunk in relevant_chunks:
            url = chunk.payload.get("source_url")

            if url and url not in sources:
                sources.append(url)

        return {
            "answer": answer,
            "sources": sources,
            "matched": True,
            "standalone_question": standalone_question,
        }