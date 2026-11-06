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

### Premier dépôt GitHub

#### Q13 Pourquoi base_vectorielle/ n'est-il pas envoyé sur GitHub ?

La base vectorielle n'est pas du code source : c'est un résultat produit à partir des documents par le script d'indexation. Elle est binaire, donc illisible dans un diff, et elle peut devenir lourde. Elle change à chaque réindexation et dépend de la version de Chroma et du modèle d'embedding. En entreprise, elle contient aussi le texte des documents internes, qu'on ne veut pas publier. On la met donc dans le `.gitignore`.

Un collègue qui clone le dépôt crée son environnement virtuel, installe les dépendances avec `pip install -r requirements.txt`, puis lance `python rag-altea/etape4_indexation.py`. Le script relit les documents, les découpe, calcule les embeddings et reconstruit la base à l'identique.

## Exercice 2

### Étape 5 — Recherche

#### Q1. Fonction rechercher

Le code est dans `rag-altea/etape5_recherche.py`. `rechercher` transforme la question en vecteur, interroge la collection avec un filtre facultatif sur le service, et renvoie pour chaque extrait son texte, sa source, sa page, son service et un score égal à 1 − distance. Plus ce score est proche de 1, plus l'extrait est proche de la question.

| Question | 1er résultat | 2e résultat | 3e résultat |
|---|---|---|---|
| Combien de jours de télétravail par semaine ? | teletravail.pdf p.1 (0,71) | conges_absences.pdf p.1 (0,62) | conges_absences.pdf p.1 (0,58) |
| Comment me connecter au VPN depuis chez moi ? | vpn.txt p.1 (0,73) | vpn.txt p.1 (0,73) | vpn.txt p.1 (0,60) |
| À quelle heure ouvre le site de Lyon ? | horaires.txt p.1 (0,76) | restauration.txt p.1 (0,58) | demande_materiel.txt p.1 (0,57) |

Le bon document arrive en tête pour les trois questions.

#### Q2 k = 1, 3 et 10

Sur la question « Quel est le plafond de remboursement d'un repas ? », k = 1 ne renvoie que `notes_de_frais.pdf` p.2, qui décrit la procédure de remboursement mais pas les montants. Avec k = 3, on récupère aussi la page 1, qui contient le tableau des plafonds (20 €, 30 €, 50 €). Avec k = 10, on obtient en plus des extraits de `mutuelle.pdf`, `restauration.txt` ou `horaires.txt`, dont les scores descendent jusqu'à 0,28 et qui n'ont rien à voir avec la question.

Quand k augmente, on a plus de chances que la bonne information soit dans les extraits : on gagne en rappel. En échange, on ajoute du bruit qui peut égarer le LLM, le prompt devient plus long et la génération plus lente. Une valeur autour de 3 est un bon compromis pour ce corpus.

#### Q3 Filtre par service

Avec `service="RH"`, la question sur le télétravail donne le même résultat que sans filtre : `teletravail.pdf` arrive en tête avec un score de 0,71. Avec `service="IT"`, la recherche ne peut plus voir les documents RH. Elle renvoie quand même trois extraits (`demande_materiel.txt`, `securite_emails.txt`), mais avec des scores faibles d'environ 0,42 et sans rapport avec la question. La recherche renvoie toujours k résultats, même quand aucun n'est pertinent.

Ce filtre est une première étape vers la confidentialité, car il permet de limiter un utilisateur aux documents de son périmètre. Un salarié qui n'a pas accès aux documents RH ne recevrait jamais d'extrait RH dans sa réponse. Il ne suffit pas pour autant. Ici, c'est le programme qui choisit le service, sans savoir qui pose la question : il n'y a ni authentification ni gestion des droits. Les documents restent tous dans la même base, lisible par quiconque y a accès. Enfin, la notion de service est trop grossière : un document RH peut être public pour tous, alors qu'un autre, comme une fiche de paie, ne doit être visible que par une seule personne. Une vraie solution associe à chaque chunk des droits d'accès vérifiés à partir de l'identité de l'utilisateur, ou utilise des bases séparées.

### Étape 6 — Génération

#### Q4. Prompt complet

Le code est dans `rag-altea/etape6_generation.py`. `construire_prompt` numérote chaque extrait sous la forme `[i] (source, page)`, suivi de son texte et d'une ligne vide. Prompt envoyé pour « Combien de jours de télétravail par semaine ? » (extraits abrégés) :

```
Tu es l'assistant interne d'Altéa Services.
Réponds à la question en utilisant UNIQUEMENT les extraits ci-dessous.
Après chaque information, indique le numéro de l'extrait entre crochets, par exemple [1].
Si les extraits ne contiennent pas la réponse, réponds exactement : "Je ne trouve pas cette information dans la documentation."
Extraits :
[1] (teletravail.pdf, page 1)
... Chaque salarié éligible peut télétravailler jusqu'à 2 jours par semaine. ...

[2] (conges_absences.pdf, page 1)
... 30 jours ouvrables (5 semaines) pour une année complète. ...

[3] (conges_absences.pdf, page 1)
... au moins 1 mois à l'avance pour une absence de plus d'une semaine.

Question : Combien de jours de télétravail par semaine ?
Réponse :
```

Les quatre premières lignes forment la consigne : le rôle de l'assistant, l'obligation de n'utiliser que les extraits, la citation des sources et la phrase de repli. Viennent ensuite les extraits numérotés renvoyés par la recherche, avec leur source et leur page. La question du salarié termine le prompt, suivie de « Réponse : » pour que le modèle enchaîne.

#### Q5. Cinq questions dont deux sans réponse

| Question | Réponse juste ? | Sources citées ? | Phrase de repli quand il le fallait ? |
|---|---|---|---|
| Combien de jours de télétravail par semaine ? | Oui (2 jours, 1 pour les alternants) | Oui, mais le « 2 jours » est attribué à [2] au lieu de [1] | Non concerné |
| Comment réinitialiser mon mot de passe ? | Oui | Non, aucun numéro d'extrait | Non concerné |
| Quel est le plafond pour un repas du midi en déplacement ? | Non, répond par la phrase de repli alors que la réponse (20 €) est dans l'extrait [2] | Non | Non, repli à tort |
| Quel temps fera-t-il demain ? | Oui | Non concerné | Oui |
| Quel est le salaire du directeur général ? | Oui | Non concerné | Oui |

Le modèle respecte bien la consigne de repli pour les questions hors documentation. En revanche, il cite mal ou pas du tout ses sources. Pour le repas du midi, le découpage a coupé le tableau au milieu du libellé (« …en déplacem » | « ent 20 € par repas »). L'extrait reçu commence donc par « 20 € par repas » sans dire de quel repas il s'agit, et le modèle préfère le repli.

#### Q6 LLM seul et hallucination

Posée directement à llama3.2, la question « Combien de jours de télétravail par semaine sont autorisés chez Altéa ? » obtient : « Je ne peux pas fournir d'informations sur les politiques d'entreprise spécifiques… ». Avec le RAG, la réponse est « Chaque salarié éligible peut télétravailler jusqu'à 2 jours par semaine », ce qui est exact. Ici le modèle seul a refusé au lieu d'inventer, mais il ne sait rien d'Altéa, qui ne figure pas dans ses données d'entraînement : un autre modèle, ou le même avec une question formulée autrement, aurait très bien pu répondre « 2 à 3 jours » avec assurance.

Une hallucination est une réponse fausse ou inventée que le modèle formule avec la même assurance qu'une réponse juste. Le RAG la limite en donnant au modèle les extraits des vrais documents et en lui demandant de ne répondre qu'à partir d'eux, avec une phrase de repli quand l'information manque. La citation des sources permet en plus au salarié de vérifier la réponse.

#### Q7 Pourquoi temperature=0 ?

La température règle la part de hasard dans le choix des mots du modèle. À 0, le modèle prend toujours le mot le plus probable : la même question donne la même réponse, et il s'en tient au plus près des extraits. Pour un assistant documentaire, on veut des réponses exactes, reproductibles et vérifiables, pas de la créativité. Une température plus élevée augmente le risque que le modèle reformule un chiffre de travers ou invente un détail. Elle rendrait aussi l'évaluation de l'étape 7 instable, puisque deux exécutions pourraient donner des résultats différents.

### Étape 7 — Évaluation

#### Q8. Fichier evaluation.csv

Le fichier `rag-altea/evaluation.csv` contient les 10 questions du corrigé, formulées comme un salarié les poserait, avec le document qui contient la réponse. Les questions qui contiennent une virgule sont entre guillemets pour que le CSV reste lisible.

#### Q9. Taux de réussite de la recherche

Le code est dans `rag-altea/etape7_evaluation.py`. Une question est réussie si le document attendu figure parmi les sources des k extraits renvoyés.

| k | Questions où le bon document est trouvé |
|--:|--:|
| 1 | 90 % |
| 3 | 100 % |
| 5 | 100 % |

Le seul échec à k = 1 est « Comment adhérer à la mutuelle ? », pour laquelle `charte_informatique.pdf` arrive devant `mutuelle.pdf`.

#### Q10. Notation des 10 réponses générées

Avec les réglages retenus (chunks de 500, k = 3), voici les réponses obtenues par `python rag-altea/etape7_evaluation.py --reponses`, comparées aux réponses du corrigé :

| Question | Réponse | Sources exactes ? |
|---|---|---|
| Télétravail par semaine | Partielle : 2 jours, mais oublie « jamais le mardi » | Non, le « 2 jours » est attribué à [2] (conges_absences.pdf) |
| Réinitialiser son mot de passe | Juste | Oui [1] |
| Poser un congé | Juste | Non, aucune citation |
| Plafond d'un repas | Fausse : phrase de repli | Non |
| Adhérer à la mutuelle | Fausse : « l'adhésion est automatique » au lieu du bulletin à rendre sous 30 jours | Non, aucune citation |
| Problème de VPN | Fausse : phrase de repli | Non |
| Nouvel ordinateur | Juste | Oui [2] |
| E-mail suspect | Juste | Non, aucune citation |
| Ouverture du site de Lyon | Juste | Oui [1] |
| Fumer dans les locaux | Juste | Oui [1] |

On obtient 60 % de réponses justes (6 sur 10, plus une partielle) et 40 % de réponses correctement sourcées (4 sur 10). La recherche trouve le bon document pour toutes les questions à k = 3, mais la génération perd beaucoup en route.

#### Q11 Analyse d'une réponse fausse

Pour « Mon VPN ne fonctionne pas, que faire ? », l'assistant a répondu par la phrase de repli. Pourtant, à l'étape 5, les trois extraits renvoyés venaient tous de `vpn.txt` : le bon document avait été trouvé, l'erreur vient donc de la génération. Avec des chunks de 500 caractères, la liste « Je n'arrive pas à me connecter au VPN : que faire ? » est coupée en plusieurs morceaux, si bien qu'aucun extrait ne contient à la fois la question et les étapes de dépannage, et le petit modèle llama3.2 préfère le repli. Le même problème explique l'échec sur le repas, où le tableau des plafonds est coupé au milieu d'un libellé.

L'amélioration testée consiste à agrandir les chunks à 1000 caractères avec 100 de chevauchement, pour qu'une section entière tienne dans un seul extrait, en gardant k = 3. La réponse VPN devient juste : elle reprend les vérifications (connexion internet, heure de l'ordinateur, réseau public, redémarrage) et le poste 4444. Sur les 10 questions, la recherche reste à 100 %, on passe à 70 % de réponses justes (7 sur 10, plus deux partielles) et à 70 % de réponses correctement sourcées. La question sur la mutuelle reste fausse, et le modèle y invente même des étapes et un extrait [6] qui n'existe pas. La section « Comment adhérer » n'est pas dans les extraits renvoyés. Il faudrait donc aussi améliorer la recherche pour cette question, par exemple en retirant les en-têtes répétés (Q4) ou en augmentant k.

### Étape 8 — Mise à disposition et GitHub

#### Q12. Interface Streamlit

Le code est dans `rag-altea/app.py` et se lance avec `streamlit run rag-altea/app.py`. La page affiche un champ de question, puis la réponse générée et, sous le titre « Sources », un bloc dépliable par extrait, intitulé « [i] source, page X ». Une fois déplié, il montre le service, le score et le texte de l'extrait. Pour « À quelle heure ouvre le site de Lyon ? », l'application répond « Le site de Lyon ouvre à 7 h 30. [1] », avec `horaires.txt`, page 1 comme premier extrait.

#### Q13. README et publication

Le `README.md` à la racine du dépôt présente l'objectif du projet, l'installation, l'ordre de lancement des scripts, un exemple de question, les résultats de l'étape 7, les limites connues et les auteurs. Le fichier `requirements.txt` est généré avec `pip freeze`. Le projet est ensuite publié avec un commit, un `git push` et le tag `v1.0`.

#### Q14 Points à traiter avant un déploiement à tous les salariés

Les droits d'accès selon le salarié sont le premier point. Aujourd'hui, tout le monde peut interroger tous les documents. Il faut identifier l'utilisateur, par exemple via l'annuaire de l'entreprise, et filtrer les chunks selon ses droits avant qu'ils n'arrivent au LLM.

Les données personnelles dans les documents posent un deuxième problème. Des documents RH peuvent contenir des noms, des salaires ou des informations de santé. Il faut les repérer et les anonymiser ou les exclure avant l'indexation, et respecter le RGPD, notamment pour la conservation des questions posées.

La mise à jour des documents doit aussi être automatisée. Une procédure doit détecter les documents ajoutés, modifiés ou supprimés, retirer leurs anciens chunks et les réindexer. Sinon, l'assistant donnera avec assurance des règles qui ne sont plus en vigueur.

Enfin, il faut chiffrer le coût et l'hébergement du LLM. Un modèle local comme llama3.2 garde les données en interne, mais il demande des serveurs avec GPU pour répondre vite à des centaines de salariés, et sa qualité reste limitée. Un modèle en ligne est meilleur mais envoie les documents à un tiers et se paie à l'usage. Le choix dépend du budget et de la sensibilité des données.
