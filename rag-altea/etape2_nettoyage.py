# etape2_nettoyage.py
import re

from etape1_collecte import collecter


def nettoyer(texte):
    texte = re.sub(r"[ \t]+", " ", texte)        # plusieurs espaces -> un seul
    texte = re.sub(r"\n{3,}", "\n\n", texte)     # 3 sauts de ligne ou plus -> 2
    texte = re.sub(r"-\n(\w)", r"\1", texte)     # recoller les mots coupés en fin de ligne
    return texte.strip()


def nettoyer_pages(pages):
    pages_propres = []
    for p in pages:
        texte = nettoyer(p["texte"])
        if texte:  # on supprime les pages devenues vides
            pages_propres.append({**p, "texte": texte})
    return pages_propres


if __name__ == "__main__":
    pages = collecter()
    pages_propres = nettoyer_pages(pages)

    # Q3 : nettoyage de toutes les pages et suppression des pages vides
    print(len(pages), "pages lues,", len(pages_propres), "pages après nettoyage,",
          len(pages) - len(pages_propres), "page(s) vide(s) supprimée(s)")

    # Q4 : une même page avant et après nettoyage
    avant = next(p for p in pages if p["source"] == "teletravail.pdf" and p["page"] == 1)
    apres = next(p for p in pages_propres if p["source"] == "teletravail.pdf" and p["page"] == 1)
    print("\n===== AVANT =====")
    print(repr(avant["texte"]))
    print("\n===== APRÈS =====")
    print(repr(apres["texte"]))
