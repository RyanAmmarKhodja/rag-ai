## Exercice 1 
### Étape 1 — Collecte

#### Q1. Nombre de pages lues pour chaque document

Le code est dans `rag-altea/etape1_collecte.py`. Les PDF sont lus page par page avec `extract_text()`. Chaque fichier texte compte comme une seule page. Le nom du dossier parent donne le service.

#### Q2 Pourquoi conserver le nom du fichier, la page et le service, et pas seulement le texte ?

Le texte seul ne dit pas d'où vient l'information. Or l'assistant doit toujours indiquer de quel document vient sa réponse. Ces métadonnées suivent chaque morceau de texte jusque dans la base vectorielle. Si on ne les garde pas dès la collecte, elles sont perdues.

Premier usage : citer la source à la fin de la réponse, par exemple « teletravail.pdf, page 1 ». Le salarié peut ainsi vérifier l'information dans le document d'origine. Second usage : filtrer la recherche par service, par exemple ne chercher que dans les documents RH. Les résultats sont plus pertinents, et c'est un premier pas vers la gestion des droits d'accès.

### Étape 2 — Nettoyage

#### Q3. Nettoyage de toutes les pages

Le code est dans `rag-altea/etape2_nettoyage.py`. La fonction `nettoyer` réduit les espaces multiples à un seul, ramène trois sauts de ligne ou plus à deux et recolle les mots coupés par un tiret en fin de ligne. `nettoyer_pages` l'applique aux 23 pages et retire celles qui deviennent vides. Aucune page n'est vide dans ce corpus, il en reste donc 23. Le texte extrait est déjà assez propre : le nettoyage retire surtout le saut de ligne final de chaque page.

#### Q4 Une même page avant et après nettoyage

Début de la page 1 de `teletravail.pdf`, qui est identique avant et après nettoyage :

```
Altéa Services — Document interne — Diffusion restreinte
1
Document fictif réalisé à des fins pédagogiques
Télétravail
RH-004 — accord télétravail — en vigueur au 1er septembre 2025
...
```

Un défaut reste : l'en-tête « Altéa Services — Document interne — Diffusion restreinte », le numéro de page seul sur sa ligne et le pied de page « Document fictif réalisé à des fins pédagogiques » se répètent en haut de chaque page de PDF. Ce texte n'apporte aucune information. Il va pourtant se retrouver dans les chunks et rapprocher artificiellement des documents qui n'ont rien à voir. Pour le corriger, on supprime toute ligne qui apparaît à l'identique sur toutes les pages d'un même document, ainsi que les lignes qui ne contiennent qu'un nombre (motif `^\d+$`).

### Étape 3 — Découpage

#### Q5. Fonction decouper

Le code est dans `rag-altea/etape3_decoupage.py`. Chaque morceau va de `debut` à `fin = debut + taille`, puis le morceau suivant repart de `fin - chevauchement`. `decouper("abcdefghij", taille=4, chevauchement=1)` renvoie bien `["abcd", "defg", "ghij"]`.

À la main : on part de l'indice 0 et on prend 4 caractères, soit « abcd » (indices 0 à 3). La fin vaut 4, on n'a pas atteint la longueur 10, donc on repart de 4 − 1 = 3 et on prend « defg » (indices 3 à 6). La fin vaut 7, on repart de 6 et on prend « ghij » (indices 6 à 9). La fin vaut 10, le texte est entièrement couvert et la boucle s'arrête. Chaque morceau commence par la dernière lettre du précédent, c'est le chevauchement d'un caractère.

#### Q6. Découpage du corpus avec trois tailles

| Taille (caractères) | Chevauchement | Nombre de chunks | Longueur moyenne |
|--------------------:|--------------:|-----------------:|-----------------:|
| 200  | 20  | 156 | 189,3 |
| 500  | 50  | 69  | 422,7 |
| 1000 | 100 | 38  | 746,4 |

La longueur moyenne est inférieure à la taille parce que le dernier morceau de chaque page est plus court. Avec 1000 caractères, la plupart des pages ne donnent qu'un ou deux chunks.

#### Q7 Taille des chunks et chevauchement

Un chunk trop petit perd son contexte. Une phrase isolée comme « 20 € le midi » ne dit plus de quoi elle parle, ce qui rend la recherche moins fiable et oblige à envoyer beaucoup de morceaux au LLM. Un chunk trop grand mélange plusieurs sujets. Son vecteur devient une moyenne floue, moins proche de chaque question précise, et il remplit le prompt de texte inutile.

Le chevauchement évite qu'une information coupée à la frontière entre deux chunks soit perdue : la fin d'un morceau est répétée au début du suivant, si bien qu'une phrase coupée reste lisible en entier dans l'un des deux.

On retient une taille de 500 caractères avec 50 de chevauchement. Cela correspond à peu près à un paragraphe ou une section du corpus. C'est assez long pour garder le contexte et assez court pour rester centré sur un seul sujet, avec 69 chunks au total.

### Étape 4 — Embeddings et indexation

#### Q8. Dimension d'un vecteur

`vecteurs.shape` affiche `(3, 384)` : chaque phrase devient un vecteur de 384 nombres avec le modèle `paraphrase-multilingual-MiniLM-L12-v2`. Avec la taille retenue (500 caractères, chevauchement 50), le corpus donne 69 chunks. Il faut donc stocker 69 × 384 = 26 496 nombres.

#### Q9 Matrice de similarité

```
[[ 1.0000,  0.4888, -0.0353],
 [ 0.4888,  1.0000, -0.0020],
 [-0.0353, -0.0020,  1.0000]]
```

Les phrases 1 (« Comment poser un jour de congé ? ») et 2 (« Quelle est la procédure pour demander des vacances ? ») sont proches, avec une similarité de 0,49. La phrase 3 sur le VPN n'est proche d'aucune des deux, avec un score autour de 0. Les phrases 1 et 2 n'ont presque aucun mot en commun, mais elles veulent dire la même chose. Le modèle d'embedding a appris sur de grandes quantités de texte que « congé » et « vacances », ou « poser » et « demander », s'emploient dans les mêmes contextes. Il compare donc le sens des phrases et non leurs mots. C'est ce qui permet à l'assistant de trouver le bon document même quand le salarié n'utilise pas le vocabulaire exact de la documentation.

#### Q10. Indexation complète

La partie B de `rag-altea/etape4_indexation.py` enchaîne la collecte, le nettoyage, le découpage en 500/50, puis le calcul des embeddings et l'`upsert` dans la collection Chroma `altea`, stockée dans `rag-altea/base_vectorielle/`. Chaque chunk est enregistré avec ses métadonnées `source`, `page` et `service`. Le script affiche 69 chunks produits et 69 chunks indexés, et un `assert` vérifie que les deux nombres sont égaux.

#### Q11. Première recherche

Pour « Combien de jours de télétravail ? », le premier résultat est `teletravail.pdf` p.1 (distance 0,32), devant deux extraits de `conges_absences.pdf` p.1 qui parlent aussi de « jours ». Pour « J'ai oublié mon mot de passe, que faire ? », on obtient `mot_de_passe.txt` (0,30), puis `charte_informatique.pdf` p.1 et `securite_emails.txt`. Pour « Quel est le plafond de remboursement d'un repas ? », les deux premiers résultats viennent de `notes_de_frais.pdf` (p.2 puis p.1, 0,47 et 0,52), suivis de `restauration.txt`. Le bon document arrive en tête à chaque fois. On remarque cependant que pour les repas, le chunk qui contient vraiment les montants (20 €, 30 €, 50 €) n'arrive qu'en deuxième position. Le premier parle de la procédure de remboursement, plus proche du mot « remboursement » de la question.

#### Q12 Relancer l'indexation

Après une deuxième exécution, la base contient toujours 69 chunks : le nombre ne double pas. Chaque chunk a un identifiant stable (`teletravail.pdf-p1-0`, etc.), et `upsert` remplace le chunk s'il existe déjà et l'ajoute sinon. Avec `add`, une deuxième exécution tenterait d'insérer des identifiants déjà présents. On obtiendrait des erreurs ou des doublons, et la recherche renverrait plusieurs fois le même texte.

Le jour où un document est modifié, il faut le réindexer. Si on se contente de relancer l'upsert et que la nouvelle version donne moins de chunks, les anciens chunks en trop restent dans la base avec un contenu périmé. Il faut donc d'abord supprimer tous les chunks de ce document (`collection.delete(where={"source": "teletravail.pdf"})`), puis réindexer la nouvelle version.
