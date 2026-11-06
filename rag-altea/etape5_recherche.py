# etape5_recherche.py
from pathlib import Path

import chromadb
from sentence_transformers import SentenceTransformer

DOSSIER_BASE = Path(__file__).resolve().parent / "base_vectorielle"

modele = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
collection = chromadb.PersistentClient(path=str(DOSSIER_BASE)).get_collection("altea")


def rechercher(question, k=3, service=None):
    vecteur = modele.encode([question]).tolist()
    filtre = {"service": service} if service else None
    res = collection.query(query_embeddings=vecteur, n_results=k, where=filtre)
    resultats = []
    for texte, meta, distance in zip(res["documents"][0], res["metadatas"][0], res["distances"][0]):
        resultats.append({
            "texte": texte,
            "source": meta["source"],
            "page": meta["page"],
            "service": meta["service"],
            "score": 1 - distance,  # plus le score est proche de 1, plus c'est proche
        })
    return resultats


def afficher(question, k=3, service=None):
    print(f"\n=== {question}  (k={k}, service={service})")
    for r in rechercher(question, k, service):
        print(f"  {r['source']:<26} p.{r['page']}  [{r['service']:<7}] score={r['score']:.3f}")


if __name__ == "__main__":
    # Q1 : trois questions de salariés
    afficher("Combien de jours de télétravail par semaine ?")
    afficher("Comment me connecter au VPN depuis chez moi ?")
    afficher("À quelle heure ouvre le site de Lyon ?")

    # Q2 : k = 1, 3 et 10 sur une même question
    for k in (1, 3, 10):
        afficher("Quel est le plafond de remboursement d'un repas ?", k=k)

    # Q3 : une question RH filtrée sur RH, puis sur IT
    afficher("Combien de jours de télétravail par semaine ?", service="RH")
    afficher("Combien de jours de télétravail par semaine ?", service="IT")
