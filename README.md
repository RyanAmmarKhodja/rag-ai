# Assistant documentaire Altéa (RAG)

Prototype d'assistant qui répond aux questions des salariés de l'entreprise fictive Altéa Services à partir de sa documentation interne. Il indique toujours de quel document vient la réponse. Le projet suit les 8 étapes d'un RAG : collecte, nettoyage, découpage, embeddings et indexation, recherche, génération, évaluation et mise à disposition.

Le corpus (`corpus_altea/docs/`) contient 15 documents internes fictifs (PDF et texte), répartis en trois services : RH, IT et Général.

## Installation

Prérequis : Python 3.10 ou plus et [Ollama](https://ollama.com) installé en local.

```bash
git clone git@github.com:RyanAmmarKhodja/rag-ai.git
cd rag-ai
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
ollama pull llama3.2
```

## Ordre de lancement

La base vectorielle n'est pas versionnée. Il faut la construire une première fois :

```bash
python rag-altea/etape4_indexation.py     # étapes 1 à 4 : crée rag-altea/base_vectorielle/
```

Puis, selon le besoin :

```bash
python rag-altea/etape5_recherche.py      # recherche seule (source, page, score)
python rag-altea/etape6_generation.py     # réponses générées par le LLM
python rag-altea/etape7_evaluation.py     # taux de réussite de la recherche (--reponses pour les réponses)
streamlit run rag-altea/app.py            # interface web
```

Les scripts `etape1_collecte.py`, `etape2_nettoyage.py` et `etape3_decoupage.py` peuvent aussi être lancés seuls pour afficher le résultat de chaque étape.

## Exemple

Question : « À quelle heure ouvre le site de Lyon ? »

Réponse : « Le site de Lyon ouvre à 7 h 30. [1] », avec comme source [1] `horaires.txt`, page 1.

## Résultats de l'évaluation (étape 7)

Réglages : chunks de 500 caractères avec 50 de chevauchement, modèle d'embedding `paraphrase-multilingual-MiniLM-L12-v2`, LLM `llama3.2` à température 0, k = 3. L'évaluation porte sur les 10 questions de `rag-altea/evaluation.csv`.

| Mesure | Résultat |
|---|---|
| Bon document trouvé (k = 1 / 3 / 5) | 90 % / 100 % / 100 % |
| Réponses justes | 60 % |
| Réponses correctement sourcées | 40 % |
| Avec des chunks de 1000 / 100 : réponses justes | 70 % |
| Avec des chunks de 1000 / 100 : réponses sourcées | 70 % |

## Limites connues

Le petit modèle llama3.2 cite souvent mal ses sources et répond parfois par la phrase de repli alors que l'information est dans les extraits. Les en-têtes, pieds de page et numéros de page des PDF ne sont pas retirés, et les tableaux sont mal restitués par l'extraction texte. Le découpage par nombre de caractères peut couper une liste ou un tableau en deux. Le filtre par service ne remplace pas une vraie gestion des droits d'accès. Enfin, quand un document est modifié, il faut supprimer ses anciens chunks avant de le réindexer.

## Auteurs

Ryan Ammar Khodja
