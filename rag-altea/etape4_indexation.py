# etape4_indexation.py
from pathlib import Path

import chromadb
from sentence_transformers import SentenceTransformer, util

from etape1_collecte import collecter
from etape2_nettoyage import nettoyer_pages
from etape3_decoupage import decouper_pages

DOSSIER_BASE = Path(__file__).resolve().parent / "base_vectorielle"

# ---------- Partie A : découvrir les embeddings ----------
modele = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")

phrases = [
    "Comment poser un jour de congé ?",
    "Quelle est la procédure pour demander des vacances ?",
    "Mon ordinateur ne se connecte pas au VPN.",
]
vecteurs = modele.encode(phrases)
print(vecteurs.shape)
print(util.cos_sim(vecteurs, vecteurs))

# ---------- Partie B : ranger les chunks dans la base vectorielle ----------
# Étapes 1 à 3 : collecte, nettoyage, découpage (taille retenue : 500 / 50)
pages = nettoyer_pages(collecter())
chunks = decouper_pages(pages, taille=500, chevauchement=50)
print(len(chunks), "chunks produits")

client = chromadb.PersistentClient(path=str(DOSSIER_BASE))
collection = client.get_or_create_collection("altea", metadata={"hnsw:space": "cosine"})

textes = [c["texte"] for c in chunks]
vecteurs = modele.encode(textes, show_progress_bar=True).tolist()

# Q8 : dimension et nombre de valeurs à stocker
dimension = len(vecteurs[0])
print("dimension :", dimension, "| nombres à stocker :", len(chunks), "x", dimension, "=", len(chunks) * dimension)

collection.upsert(
    ids=[c["id"] for c in chunks],
    documents=textes,
    embeddings=vecteurs,
    metadatas=[{"source": c["source"], "page": c["page"], "service": c["service"]} for c in chunks],
)
print(collection.count(), "chunks indexés")

# Q10 : le nombre de chunks indexés doit être égal au nombre de chunks produits
assert collection.count() == len(chunks), "nombre de chunks indexés différent du nombre produit"

# ---------- Q11 : première recherche ----------
questions = [
    "Combien de jours de télétravail ?",
    "J'ai oublié mon mot de passe, que faire ?",
    "Quel est le plafond de remboursement d'un repas ?",
]
for question in questions:
    resultat = collection.query(
        query_embeddings=modele.encode([question]).tolist(), n_results=3
    )
    print(f"\n=== {question}")
    for doc, meta, dist in zip(resultat["documents"][0], resultat["metadatas"][0], resultat["distances"][0]):
        extrait = doc[:120].replace("\n", " ")
        print(f"  [{meta['source']} p.{meta['page']} | {meta['service']}] distance={dist:.3f}")
        print(f"     {extrait}…")
