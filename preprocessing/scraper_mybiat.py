"""
Scrapes MyBIAT help-center pages into two files:
  - mybiat_phone.txt  (MyBIAT Mobile section)
  - mybiat_web.txt    (MyBIAT Web section)

Each page's content is separated by a clear header with its source URL,
so you keep traceability for citations later in the RAG pipeline.
"""

import requests
from bs4 import BeautifulSoup
import re
import time

HEADERS = {"User-Agent": "Mozilla/5.0"}

# ---- MyBIAT Mobile links (name: url) ----
mobile_links = {
    "Paiement factures STEG / SONEDE": "https://www.mybiat.tn/fr/version-mobile-uniquement/paiement-factures-steg-sonede",
    "Produits - Mes produits": "https://www.mybiat.tn/fr/version-web-et-mobile/mes-produits",
    "Produits - Comptes": "https://www.mybiat.tn/fr/version-web-et-mobile/comptes",
    "Produits - Crédits": "https://www.mybiat.tn/fr/version-web-et-mobile/credits",
    "Produits - Allocations voyages d'affaires (AVA)": "https://www.mybiat.tn/fr/version-web-et-mobile/allocations-voyages-daffaires-ava",
    "Produits - Placements bancaires": "https://www.mybiat.tn/fr/version-web-et-mobile/placements-bancaires",
    "Produits - Placements titres": "https://www.mybiat.tn/fr/version-web-et-mobile/placements-titres",
    "Produits - Projet Avenir": "https://www.mybiat.tn/fr/version-web-et-mobile/projet-avenir",
    "Recharge téléphonique Orange": "https://www.mybiat.tn/fr/version-mobile-uniquement/recharge-telephonique-orange",
    "Recharge Tunisie Autoroutes": "https://www.mybiat.tn/fr/version-mobile-uniquement/recharge-tunisie-autoroutes",
    "Cartes - Mes cartes": "https://www.mybiat.tn/fr/version-web-et-mobile/mes-cartes",
    "Cartes - Avantages des cartes": "https://www.mybiat.tn/fr/version-mobile-uniquement/avantages-des-cartes",
    "Cartes - Chargement des cartes prépayées": "https://www.mybiat.tn/fr/version-web-et-mobile/chargement-des-cartes-prepayees",
    "Opérations - Les opérations": "https://www.mybiat.tn/fr/version-web-et-mobile/les-operations",
    "Opérations - Filtres sur opérations": "https://www.mybiat.tn/fr/version-web-et-mobile/filtres-sur-operations",
    "Opérations - Détails des opérations": "https://www.mybiat.tn/fr/version-web-et-mobile/details-des-operations",
    "Opérations - En cours de dénouement": "https://www.mybiat.tn/fr/version-web-et-mobile/operations-en-cours-de-denouement",
    "Opérations - Annulées": "https://www.mybiat.tn/fr/version-web-et-mobile/operations-annulees",
    "Chéquiers - Gestion des chéquiers": "https://www.mybiat.tn/fr/version-web-et-mobile/gestion-des-chequiers",
    "Chéquiers - Association RIB TuniChèque": "https://www.mybiat.tn/fr/version-mobile-uniquement/association-rib-tunicheque",
    "Téléchargement - Vos documents": "https://www.mybiat.tn/fr/version-web-et-mobile/telechargement-de-vos-documents",
    "Téléchargement - Transactions": "https://www.mybiat.tn/fr/version-web-et-mobile/telechargement-des-transactions",
    "Téléchargement - RIB/IBAN": "https://www.mybiat.tn/fr/version-web-et-mobile/telechargement-du-ribiban",
    "Téléchargement - Relevé produits de placement": "https://www.mybiat.tn/fr/version-web-et-mobile/telechargement-releve-produits-de-placement",
    "Téléchargement - Justificatif de virement": "https://www.mybiat.tn/fr/version-web-et-mobile/telechargement-du-justificatif-de-virement",
    "Téléchargement - Justificatif de chargement de carte": "https://www.mybiat.tn/fr/version-web-et-mobile/telechargement-du-justificatif-de-chargement-de-carte",
    "Téléchargement - Attestation d'assistance voyage": "https://www.mybiat.tn/fr/version-web-et-mobile/telechargement-de-lattestation-dassistance-voyage",
    "Téléchargement - Extrait AVA": "https://www.mybiat.tn/fr/version-web-et-mobile/telechargement-de-lextrait-ava",
    "Téléchargement - Attestation de versement Projet Avenir": "https://www.mybiat.tn/fr/version-mobile-uniquement/telechargement-de-lattestation-de-versement-projet-avenir",
    "Simulateur de crédit": "https://www.mybiat.tn/fr/version-mobile-uniquement/simulateur-de-credit",
    "Géolocalisation des agences": "https://www.mybiat.tn/fr/version-mobile-uniquement/geolocalisation-des-agences",
    "Demande de contact": "https://www.mybiat.tn/fr/version-web-et-mobile/demande-de-contact",
    "Notifications - Centre de notifications": "https://www.mybiat.tn/fr/version-web-et-mobile/centre-de-notifications-de-mybiat",
    "Notifications - Push": "https://www.mybiat.tn/fr/version-mobile-uniquement/notifications-push",
    "Notifications - Gestion des notifications Push": "https://www.mybiat.tn/fr/version-mobile-uniquement/gestion-des-notifications-push",
}

# ---- MyBIAT Web links (name: url) ----
web_links = {
    "Accès à MyBIAT Web - Connexion": "https://www.mybiat.tn/fr/version-web-uniquement/connexion-mybiat-web",
    "Parcours d'auto-souscription à MyBIAT": "https://www.mybiat.tn/fr/version-web-uniquement/parcours-dauto-souscription-mybiat",
    "Déconnexion de MyBIAT Web": "https://www.mybiat.tn/fr/version-web-uniquement/deconnexion-de-mybiat-web",
    "Produits - Mes produits": "https://www.mybiat.tn/fr/version-web-et-mobile/mes-produits",
    "Produits - Comptes": "https://www.mybiat.tn/fr/version-web-et-mobile/comptes",
    "Produits - Crédits": "https://www.mybiat.tn/fr/version-web-et-mobile/credits",
    "Produits - Allocations voyages d'affaires (AVA)": "https://www.mybiat.tn/fr/version-web-et-mobile/allocations-voyages-daffaires-ava",
    "Produits - Placements bancaires": "https://www.mybiat.tn/fr/version-web-et-mobile/placements-bancaires",
    "Produits - Placements titres": "https://www.mybiat.tn/fr/version-web-et-mobile/placements-titres",
    "Produits - Projet Avenir": "https://www.mybiat.tn/fr/version-web-et-mobile/projet-avenir",
    "Virements - Vers mes comptes": "https://www.mybiat.tn/fr/version-web-et-mobile/virements-vers-mes-comptes",
    "Virements - Permanents et programmés": "https://www.mybiat.tn/fr/version-web-et-mobile/virements-permanents-et-programmes",
    "Virements - Vers un autre bénéficiaire": "https://www.mybiat.tn/fr/version-web-et-mobile/virement-vers-un-autre-beneficiaire",
    "Virements - Gestion des bénéficiaires": "https://www.mybiat.tn/fr/version-web-et-mobile/gestion-des-beneficiaires",
    "Virements - Validation": "https://www.mybiat.tn/fr/version-web-et-mobile/validation-des-virements",
    "Virements - Suivi": "https://www.mybiat.tn/fr/version-web-et-mobile/suivi-des-virements",
    "Cartes - Mes cartes": "https://www.mybiat.tn/fr/version-web-et-mobile/mes-cartes",
    "Cartes - Chargement des cartes prépayées": "https://www.mybiat.tn/fr/version-web-et-mobile/chargement-des-cartes-prepayees",
    "Opérations - Les opérations": "https://www.mybiat.tn/fr/version-web-et-mobile/les-operations",
    "Opérations - Filtres sur opérations": "https://www.mybiat.tn/fr/version-web-et-mobile/filtres-sur-operations",
    "Opérations - Détails des opérations": "https://www.mybiat.tn/fr/version-web-et-mobile/details-des-operations",
    "Opérations - En cours de dénouement": "https://www.mybiat.tn/fr/version-web-et-mobile/operations-en-cours-de-denouement",
    "Opérations - Annulées": "https://www.mybiat.tn/fr/version-web-et-mobile/operations-annulees",
    "Chéquiers - Gestion des chéquiers": "https://www.mybiat.tn/fr/version-web-et-mobile/gestion-des-chequiers",
    "Chéquiers - Pré-réservation chèque": "https://www.mybiat.tn/version-web-uniquement/pre-reservation-cheque",
    "Téléchargement - Vos documents": "https://www.mybiat.tn/fr/version-web-et-mobile/telechargement-de-vos-documents",
    "Téléchargement - Transactions": "https://www.mybiat.tn/fr/version-web-et-mobile/telechargement-des-transactions",
    "Téléchargement - Relevé monétique": "https://www.mybiat.tn/version-web-uniquement/telechargement-releve-monetique",
    "Téléchargement - RIB/IBAN": "https://www.mybiat.tn/fr/version-web-et-mobile/telechargement-du-ribiban",
    "Téléchargement - Relevé produits de placement": "https://www.mybiat.tn/fr/version-web-et-mobile/telechargement-releve-produits-de-placement",
    "Téléchargement - Justificatif de virement": "https://www.mybiat.tn/fr/version-web-et-mobile/telechargement-du-justificatif-de-virement",
    "Téléchargement - Justificatif de chargement de carte": "https://www.mybiat.tn/fr/version-web-et-mobile/telechargement-du-justificatif-de-chargement-de-carte",
    "Téléchargement - Attestation d'assistance voyage": "https://www.mybiat.tn/fr/version-web-et-mobile/telechargement-de-lattestation-dassistance-voyage",
    "Téléchargement - Extrait AVA": "https://www.mybiat.tn/fr/version-web-et-mobile/telechargement-de-lextrait-ava",
    "Demande de contact": "https://www.mybiat.tn/fr/version-web-et-mobile/demande-de-contact",
    "Notifications - Centre de notifications": "https://www.mybiat.tn/fr/version-web-et-mobile/centre-de-notifications-de-mybiat",
}

# cache so a URL shared between both lists is only fetched once
_page_cache = {}


# Patterns of stray text lines to drop even after removing structural junk
# (feedback widget counters, breadcrumb leftovers, etc.)
JUNK_LINE_PATTERNS = [
    r"^\d{1,2}\s+(jan|fév|mar|avr|mai|juin|juil|ao[uû]t|sep|oct|nov|déc)\.?\s*\d{4}$",  # "13 mai 2026"
    r"^(Like|Dislike|Oui|Non)$",
    r"^\d+$",  # lone vote counters
    r"^Ces informations vous ont-elles été utiles ?\??$",
    r"^Aller au contenu principal$",
]
JUNK_LINE_RE = re.compile("|".join(JUNK_LINE_PATTERNS), re.IGNORECASE)


# This exact CTA bar repeats identically on every MyBIAT help page
# (floating action menu: RDV, Devenir Client, Contact, etc.) — not real content.
BOILERPLATE_BLOCK = """Prendre un RDV
Conseiller en agence
Devenir Client
Devenir Client
Contactez-nous
Formulaire en ligne
Trouver une agence BIAT
Accéder à notre carte
Télécharger
la brochure MyBIAT
Télécharger l’application
Contactez-nous
Je recommande MyBIAT"""


def fetch_clean_text(url):
    if url in _page_cache:
        return _page_cache[url]

    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
    except requests.RequestException as e:
        text = f"[ERROR fetching page: {e}]"
        _page_cache[url] = text
        return text

    soup = BeautifulSoup(resp.text, "html.parser")

    # The real article content lives inside role="main" (Drupal main-container),
    # but that same container also wraps a news-feed block and a search-filter
    # widget which we don't want. Grab the main region, then strip those out.
    main = soup.find(attrs={"role": "main"}) or soup.find("main") or soup.body

    if main is None:
        text = "[ERROR: no main content found]"
    else:
        # structural junk: nav/menus, scripts, and known Drupal widget blocks
        for junk in main.find_all(["nav", "header", "footer", "script", "style", "form"]):
            junk.decompose()

        # id/class patterns seen in the page inspector: news feed, exposed search
        # filter, breadcrumb, and feedback ("useful?") widgets
        junk_selectors = [
            {"id": re.compile(r"block-views-block-actualite")},
            {"class": re.compile(r"views-exposed-form")},
            {"class": re.compile(r"blc_breadcrumb")},
            {"class": re.compile(r"vote-widget|voting|feedback")},
        ]
        for sel in junk_selectors:
            for junk in main.find_all(attrs=sel):
                junk.decompose()

        text = main.get_text(separator="\n", strip=True)

        # strip the repeated site-wide CTA boilerplate block
        text = text.replace(BOILERPLATE_BLOCK, "").strip()

        # text-level cleanup pass: drop stray junk lines (dates, vote counters,
        # feedback labels) that weren't caught by the structural removal above
        lines = [
            line.strip()
            for line in text.splitlines()
            if line.strip() and not JUNK_LINE_RE.match(line.strip())
        ]
        text = "\n".join(lines)

    _page_cache[url] = text
    return text


def scrape_to_file(links: dict, output_filename: str):
    with open(output_filename, "w", encoding="utf-8") as f:
        for name, url in links.items():
            print(f"Fetching: {name} -> {url}")
            content = fetch_clean_text(url)

            f.write(f"===== {name} =====\n")
            f.write(f"Source: {url}\n")
            f.write("---\n")
            f.write(content)
            f.write("\n\n")

            time.sleep(0.5)  # be polite to the server

    print(f"Done. Saved to {output_filename}\n")


if __name__ == "__main__":
    scrape_to_file(mobile_links, "mybiat_phone.txt")
    scrape_to_file(web_links, "mybiat_web.txt")