# etape7_evaluation.py
import csv
import sys
from pathlib import Path

from etape5_recherche import rechercher

FICHIER_EVAL = Path(__file__).resolve().parent / "evaluation.csv"


def lire_evaluation(fichier=FICHIER_EVAL):
    with open(fichier, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def taux_reussite(fichier=FICHIER_EVAL, k=3):
    lignes = lire_evaluation(fichier)
    trouves = 0
    for ligne in lignes:
        sources = [r["source"] for r in rechercher(ligne["question"], k)]
        if ligne["document_attendu"] in sources:  # le document attendu fait-il partie des sources trouvées ?
            trouves += 1
    return trouves / len(lignes)


if __name__ == "__main__":
    # Q9 : taux de réussite de la recherche
    for k in (1, 3, 5):
        print(f"k = {k} : {taux_reussite(k=k):.0%} de questions où le bon document est trouvé")

    # Q10 : réponses générées, à noter à la main
    if "--reponses" in sys.argv:
        from etape6_generation import repondre

        for ligne in lire_evaluation():
            texte, extraits = repondre(ligne["question"])
            sources = ", ".join(f"[{i}] {e['source']} p.{e['page']}" for i, e in enumerate(extraits, 1))
            print(f"\n=== {ligne['question']}  (attendu : {ligne['document_attendu']})")
            print(texte)
            print("   Extraits :", sources)
