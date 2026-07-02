"""
Scrapes BIAT product/service pages into biat_main.txt
"""

import requests
from bs4 import BeautifulSoup
import re
import time

HEADERS = {"User-Agent": "Mozilla/5.0"}

biat_links = {
    # ---------------- Existing links ----------------
    "Crédits - page d'accueil": "https://www.biat.tn/biat/Fr/credits_61_59",
    "Crédit Auto (CREDIAUTO)": "https://www.biat.tn/biat/Fr/crediauto_63_66",
    "Crédits Conso": "https://www.biat.tn/biat/Fr/credits-conso_62_63",
    "Crédits Immobiliers": "https://www.biat.tn/biat/Fr/credits-immobiliers_62_60",
    "BIATIMMO": "https://www.biat.tn/biat/Fr/biatimmo_63_61",
    "Crédit Awal Sakan (Premier Logement)": "https://www.biat.tn/biat/Fr/credit-awal-sakan-premier-logement_63_383",
    "CREDIRESIDENCE": "https://www.biat.tn/biat/Fr/crediresidence_63_62",
    "Crédit FLEXIMMO": "https://www.biat.tn/biat/Fr/credit-fleximmo_63_398",
    "Crédit direct à immobilier": "https://www.biat.tn/biat/Fr/credit-direct-a-immobilier_82_335",
    "Plan Epargne Résidence": "https://www.biat.tn/biat/Fr/plan-epargne-residence_63_47",
    "Simuler vos crédits": "https://www.biat.tn/biat/Fr/simuler-vos-credits_77_126",
    "Calculer capacité d'endettement": "https://www.biat.tn/biat/Fr/calculer-capacite-deendettement_84_337",
    "Simuler votre Epargne": "https://www.biat.tn/biat/Fr/simuler-votre-epargne_76_125",
    "Cours de change BBE": "https://www.biat.tn/biat/Fr/cours-de-change-bbe_66_127",
    "Cours OPCVM": "https://www.biat.tn/biat/Fr/cours-opcvm_65_128",

    # ---------------- Comptes à vue ----------------
    "Compte Chèques": "https://www.biat.tn/biat/Fr/compte-cheques_63_22",
    "Compte Etranger en devises": "https://www.biat.tn/biat/Fr/compte-etranger-en-devises_63_24",
    "Compte Etranger en Dinars Convertibles": "https://www.biat.tn/biat/Fr/compte-etranger-en-dinars-convertibles_63_25",

    # ---------------- Comptes spéciaux ----------------
    "Compte spécial en devise ou en Dinars Convertibles":
        "https://www.biat.tn/biat/Fr/compte-special-en-devise-ou-en-dinars-convertibles_63_118",
    "Compte Intérieur non Résident (INR)":
        "https://www.biat.tn/biat/Fr/compte-interieur-non-resident-inrbr_63_117",

    # ---------------- Cartes ----------------
    "Carte Technologique": "https://www.biat.tn/biat/Fr/carte-technologique_63_356",
    "Carte CHABEB": "https://www.biat.tn/biat/Fr/carte-chabeb_63_343",
    "Carte VISA ou MasterCard classique": "https://www.biat.tn/biat/Fr/carte-visa-ou-mastercard-classique_63_31",
    "Carte BIAT Flexy": "https://www.biat.tn/biat/Fr/carte-biat-flexy_63_410",
    "Carte FLY": "https://www.biat.tn/biat/Fr/carte-fly_63_358",
    "Carte CASH": "https://www.biat.tn/biat/Fr/carte-cash_63_359",
    "Carte CASH Anonyme": "https://www.biat.tn/biat/Fr/carte-cash-anonyme_63_367",
    "Carte H’DYA": "https://www.biat.tn/biat/Fr/carte-hedya_63_360",
    "Carte TRAVEL": "https://www.biat.tn/biat/Fr/carte-travel_63_35",
    "Carte VISA Premier": "https://www.biat.tn/biat/Fr/carte-visa-premier_63_32",
    "Carte MasterCard Platinum": "https://www.biat.tn/biat/Fr/carte-mastercard-platinum_63_33",
    "Carte VISA Infinite": "https://www.biat.tn/biat/Fr/carte-visa-infinite_63_347",

    # ---------------- Banque à distance ----------------
    "MyBIAT": "https://www.biat.tn/biat/Fr/mybiat_63_37",
    "MESSAGIS": "https://www.biat.tn/biat/Fr/messagis_63_38",
    "Services pratiques sur DAB": "https://www.biat.tn/biat/Fr/services-pratiques-sur-dab_63_40",

    # ---------------- Épargne ----------------
    "Compte Epargne Prévoyance": "https://www.biat.tn/biat/Fr/compte-epargne-prevoyance_63_45",
    "Compte Chèquépargne": "https://www.biat.tn/biat/Fr/compte-chequepargne_63_44",
    "Epargne WLEDNA": "https://www.biat.tn/biat/Fr/epargne-wledna_63_49",
    "Projet Avenir": "https://www.biat.tn/biat/Fr/projet-avenir_63_50",
    "Projet Avenir Etudes": "https://www.biat.tn/biat/Fr/projet-avenir-etudes_63_51",
    "Projet Avenir Retraite": "https://www.biat.tn/biat/Fr/projet-avenir-retraite_63_52",

    # ---------------- Placements ----------------
    "Placements bancaires": "https://www.biat.tn/biat/Fr/placements-bancaires_63_119",
    "Les SICAV": "https://www.biat.tn/biat/Fr/les-sicav_63_56",
    "Compte Titres": "https://www.biat.tn/biat/Fr/compte-titres_63_57",
    "Compte Epargne en Actions (CEA)": "https://www.biat.tn/biat/Fr/compte-epargne-en-actions-cea_63_58",

    # ---------------- Crédits divers ----------------
    "CREDIMEDIA": "https://www.biat.tn/biat/Fr/credimedia_63_64",
    "Avan'Salaire": "https://www.biat.tn/biat/Fr/avan-salaire_63_65",
    "CREDIAUTO": "https://www.biat.tn/biat/Fr/crediauto_63_66",
    "CREDIFOYER": "https://www.biat.tn/biat/Fr/credifoyer_63_67",
    "CREDIRENOV": "https://www.biat.tn/biat/Fr/credirenov_63_68",
    "Crédit revolving TEMPO": "https://www.biat.tn/biat/Fr/credit-revolving-tempo_63_69",
    "CREDINAJAH": "https://www.biat.tn/biat/Fr/credinajah_63_71",

    # ---------------- Assurance ----------------
    "Assurance Voyage BIAT": "https://www.biat.tn/biat/Fr/assurance-voyage-biat_63_377",
    "Bénoun": "https://www.biat.tn/biat/Fr/benoun_63_74",
    "Familia Silver": "https://www.biat.tn/biat/Fr/familia-silver_63_75",
    "Familia Gold": "https://www.biat.tn/biat/Fr/familia-gold_63_388",

    # ---------------- Packages ----------------
    "Pack Epargne": "https://www.biat.tn/biat/Fr/pack-epargne_63_389",
    "Pack University": "https://www.biat.tn/biat/Fr/pack-university_63_342",
    "Pack FIRST": "https://www.biat.tn/biat/Fr/pack-first_63_80",
    "Pack Express": "https://www.biat.tn/biat/Fr/pack-express_63_362",
    "Pack SILVER": "https://www.biat.tn/biat/Fr/pack-silver_63_79",
    "Accord SAFIR": "https://www.biat.tn/biat/Fr/accord-safir_63_78",
    "Classe Platinum": "https://www.biat.tn/biat/Fr/classe-platinum_63_350",
    "Classe ELITE": "https://www.biat.tn/biat/Fr/classe-elite_63_349",
}

_page_cache = {}

JUNK_LINE_PATTERNS = [
    r"^©\d{4}\s+BANQUE",
    r"^\d{1,2}\s+(jan|fév|mar|avr|mai|juin|juil|ao[uû]t|sep|oct|nov|déc)\.?\s*\d{4}$",
]
JUNK_LINE_RE = re.compile("|".join(JUNK_LINE_PATTERNS), re.IGNORECASE)


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

    center = (
        soup.select_one("div.content div.center")
        or soup.select_one("div.content")
        or soup.select_one("div.container")
        or soup.body
    )

    if center is None:
        text = "[ERROR: no content block found]"
        _page_cache[url] = text
        return text

    for junk in center.find_all(["script", "style", "nav", "header", "footer"]):
        junk.decompose()

    for junk in center.select("div.left, div.fil_ariane, div.box_top"):
        junk.decompose()

    text = center.get_text(separator="\n", strip=True)

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

            time.sleep(0.5)

    print(f"Done. Saved to {output_filename}\n")


if __name__ == "__main__":
    scrape_to_file(biat_links, "biat_main.txt")