# etape6_generation.py
import sys

from openai import OpenAI

from etape5_recherche import rechercher

client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")  # Ollama en local
MODELE = "llama3.2"
REPLI = "Je ne trouve pas cette information dans la documentation."


def construire_prompt(question, extraits):
    contexte = ""
    for i, e in enumerate(extraits, start=1):
        contexte += f"[{i}] ({e['source']}, page {e['page']})\n{e['texte']}\n\n"
    return f"""Tu es l'assistant interne d'Altéa Services.
Réponds à la question en utilisant UNIQUEMENT les extraits ci-dessous.
Après chaque information, indique le numéro de l'extrait entre crochets, par exemple [1].
Si les extraits ne contiennent pas la réponse, réponds exactement : "{REPLI}"
Extraits :
{contexte}
Question : {question}
Réponse :"""


def repondre(question, k=3):
    extraits = rechercher(question, k)
    prompt = construire_prompt(question, extraits)
    reponse = client.chat.completions.create(
        model=MODELE,
        temperature=0,
        messages=[{"role": "user", "content": prompt}],
    )
    return reponse.choices[0].message.content, extraits


def demander_sans_rag(question):
    reponse = client.chat.completions.create(
        model=MODELE,
        temperature=0,
        messages=[{"role": "user", "content": question}],
    )
    return reponse.choices[0].message.content


if __name__ == "__main__":
    # Q4 : prompt complet envoyé pour une question
    question = "Combien de jours de télétravail par semaine ?"
    print(construire_prompt(question, rechercher(question)))

    if "--prompt" in sys.argv:
        sys.exit()

    # Q5 : 5 questions, dont 2 sans réponse dans la documentation
    questions = [
        "Combien de jours de télétravail par semaine ?",
        "Comment réinitialiser mon mot de passe ?",
        "Quel est le plafond pour un repas du midi en déplacement ?",
        "Quel temps fera-t-il demain ?",
        "Quel est le salaire du directeur général ?",
    ]
    for q in questions:
        texte, extraits = repondre(q)
        print(f"\n=== {q}\n{texte}")
        print("   Extraits :", ", ".join(f"[{i}] {e['source']} p.{e['page']}" for i, e in enumerate(extraits, 1)))

    # Q6 : même question posée directement au LLM, sans extraits
    q = "Combien de jours de télétravail par semaine sont autorisés chez Altéa ?"
    print(f"\n=== SANS RAG : {q}\n{demander_sans_rag(q)}")
    print(f"\n=== AVEC RAG : {q}\n{repondre(q)[0]}")
