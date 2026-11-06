# etape3_decoupage.py
from etape1_collecte import collecter
from etape2_nettoyage import nettoyer_pages


def decouper(texte, taille=500, chevauchement=50):
    assert chevauchement < taille, "le chevauchement doit être plus petit que la taille"
    morceaux = []
    debut = 0
    while debut < len(texte):
        fin = debut + taille                  # fin du morceau
        morceaux.append(texte[debut:fin])
        if fin >= len(texte):
            break
        debut = fin - chevauchement           # avancer en gardant le chevauchement
    return morceaux


def decouper_pages(pages, taille=500, chevauchement=50):
    chunks = []
    for p in pages:
        for i, morceau in enumerate(decouper(p["texte"], taille, chevauchement)):
            chunks.append({
                "id": f"{p['source']}-p{p['page']}-{i}",
                "texte": morceau,
                "source": p["source"],
                "page": p["page"],
                "service": p["service"],
            })
    return chunks


if __name__ == "__main__":
    # Q5 : vérification
    resultat = decouper("abcdefghij", taille=4, chevauchement=1)
    print(resultat)
    assert resultat == ["abcd", "defg", "ghij"]

    # Q6 : découpage du corpus avec trois tailles
    pages = nettoyer_pages(collecter())
    print(f"\n{'Taille':>6} {'Chevauchement':>14} {'Nb chunks':>10} {'Long. moyenne':>14}")
    for taille, chevauchement in [(200, 20), (500, 50), (1000, 100)]:
        chunks = decouper_pages(pages, taille, chevauchement)
        moyenne = sum(len(c["texte"]) for c in chunks) / len(chunks)
        print(f"{taille:>6} {chevauchement:>14} {len(chunks):>10} {moyenne:>14.1f}")
