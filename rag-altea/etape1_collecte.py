# etape1_collecte.py
from collections import Counter
from pathlib import Path

from pypdf import PdfReader

# Dossier du corpus, résolu par rapport à ce script (fonctionne quel que soit le dossier courant)
DOSSIER_DOCS = Path(__file__).resolve().parent.parent / "corpus_altea" / "docs"


def lire_pdf(chemin):
    lecteur = PdfReader(chemin)
    pages = []
    for numero, page in enumerate(lecteur.pages, start=1):
        texte = page.extract_text() or ""
        pages.append({"source": chemin.name, "page": numero, "texte": texte})
    return pages


def lire_txt(chemin):
    texte = Path(chemin).read_text(encoding="utf-8")
    return [{"source": chemin.name, "page": 1, "texte": texte}]


def collecter(dossier=DOSSIER_DOCS):
    pages = []
    for chemin in sorted(Path(dossier).rglob("*")):
        if not chemin.is_file():
            continue
        service = chemin.parent.name  # RH, IT ou General
        extension = chemin.suffix.lower()
        if extension == ".pdf":
            pages_doc = lire_pdf(chemin)
        elif extension == ".txt":
            pages_doc = lire_txt(chemin)
        else:
            continue  # on ignore les autres types de fichiers
        for page in pages_doc:
            page["service"] = service
            pages.append(page)
    return pages


if __name__ == "__main__":
    pages = collecter()

    # Q1 : nombre de pages lues pour chaque document
    compte = Counter((p["service"], p["source"]) for p in pages)
    print(f"{'Service':<10}{'Document':<28}{'Pages':>5}")
    print("-" * 43)
    for (service, source), nb in sorted(compte.items()):
        print(f"{service:<10}{source:<28}{nb:>5}")
    print("-" * 43)
    print(len(compte), "documents,", len(pages), "pages lues")
