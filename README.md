# Projet Trivial Poursuite
** méthodologie, votre organisation de projet et le setup complet**
---------------------------------------------------------------------------------------

** NOS QUESTIONS METIER **

Dans quelles catégories le modèle est-il le plus performant ?

→ Comparer le taux de bonnes réponses (%) par catégorie (histoire, sciences, géographie, etc.).


La difficulté des questions influence-t-elle les performances et le temps de réponse du modèle ?

→ Comparer le taux de bonnes réponses (%) et le temps de réponse moyen selon le niveau de difficulté (facile, moyen, difficile).


Le type de question (Boolean ou Multiple Choice) influence-t-il les performances et le temps de réponse du modèle ?

→ Comparer le taux de bonnes réponses (%) et le temps de réponse moyen pour les questions boolean et multiple.


Le langage du prompt (français ou anglais) influence-t-il les performances et le temps de réponse du modèle ?

→ Comparer le taux de bonnes réponses (%) et le temps de réponse moyen selon la langue du prompt (français ou anglais), afin de déterminer si le modèle obtient de meilleurs résultats ou répond plus rapidement avec un prompt en anglais.


# Méthodologie
Mise en place d'une architecture en médaillon pour stocker les données de ce projet.

# **Architecture :**

- `Couche bronze` : Données brutes issues du scraping : `questions_raw.csv` réalisé grâce au fichier src/ingestion/opentdb.py
Récupération des questions depuis l’API Open Trivia Database (OpenTDB)
Stockage des données brutes dans la couche Bronze
Conservation du fichier Bronze comme source non modifiée

- `Couche silver` : fichier src/enrichment/silver_clean.py + réponses de l'IA avec le fichier src/enrichment/openAI_benchmark.py (script fr/en)
    - Silver contient des observations propres et exploitables

        Suppression des valeurs invalides (suppression des lignes où les champs essentiels sont manquants : catégorie, difficulté, question, réponse correcte ou type)

        Normalisation des champs (nettoyage des textes et mise en minuscules de certains champs)

        Suppression des doublons des questions (à partir du `question_id` créé à partir du texte de la question)

        Création d’un `question_id` (identifiant créé à partir du texte de chaque question)

        Sélection et réorganisation des colonnes utiles (conservation des informations nécessaires au benchmark)

        Conversion au format Parquet (stockage des données nettoyées dans `questions_clean.parquet`)


EXPLICATIONS :

    - Chaque question est transformée en QCM : afin de standardiser l'évaluation du modèle et d'éviter les faux négatifs liés aux différences de formulation entre la réponse du modèle et la réponse attendue. 

    - Le modèle doit répondre uniquement par A, B, C ou D

    - Deux versions du prompt sont testées : français / anglais

    - Pour chaque réponse, stockage de :

        - réponse brute du modèle

        - lettre choisie

        - bonne réponse

        - résultat correct/incorrect

        - temps de réponse

        - langue du prompt


- `Couche gold` : Données métiers (performance des prompts) --> création de la base duckdb dans warehouse
    - Gold répond directement à nos questions métier 

    - Stockage des données Gold :

    Les modèles Mart sont matérialisés dans le schéma main_gold de notre base DuckDB.

    Ils contiennent les indicateurs métiers utilisés pour répondre à nos quatre questions d’analyse :

        mart_category_performance, 
        mart_difficulty_performance, 
        mart_type_performance, 
        mart_prompt_performance


Le fichier sources.yml permet à dbt de déclarer nos données Silver comme des sources. Il fait le lien entre les noms logiques utilisés dans nos modèles dbt, comme silver.responses, et les fichiers Parquet physiques présents dans data/silver


Dans la granularité des couches Silver et Gold, on utilise l’organisation `staging`, `intermediate` et `mart` (dans une base duckdb).
Staging : première couche qui récupère et standardise les réponses du modèle, en les enrichissant avec les informations des questions.
Intermediate : couche qui prépare les indicateurs nécessaires, notamment correct_flag, qui permet d’identifier si la réponse du modèle est correcte.
Mart : couche qui répond aux questions métier en calculant les indicateurs finaux, comme le taux de réussite et le temps de réponse moyen. 


dbt_projet.yml : materialized indique sous quelle forme dbt va créer le résultat d'un modèle dans le Data Warehouse. Dans notre projet, le Staging est matérialisé en View car il sert principalement à préparer les données, tandis que l'Intermediate et les Marts sont matérialisés en Tables car leurs transformations et leurs indicateurs sont réutilisés et consommés par le dashboard.

Le dbt_project.yml configure le fonctionnement et l'organisation du projet dbt, tandis que le profiles.yml configure la connexion au Data Warehouse. Dans notre projet, le moteur est DuckDB et notre base est le fichier warehouse/trivial.duckdb.


# **Ingénierie des données :**

- Utilisation de dbt pour construire le lignage `staging → intermediate → gold`:
    -Générer les fichiers de documentation et le catalogue
        dbt docs generate
    -Lancer un serveur local pour visualiser le site dans votre navigateur
        dbt docs serve


# **Visualisation des résultats du benchmark :**
- **Streamlit** pour produire un dashboard interactif des résultats du benchmark:

        `streamlit run dashboard/app.py`

# Setup complet
- Création d’un environnement virtuel `.venv`
- Installation des dépendances depuis `requirements.txt`


- Création d’un fichier `.env` à la racine du projet
- Stockage de la clé API et de l’URL de l’API OpenAI-compatible
- Le `.env` est ajouté au `.gitignore` afin de ne pas exposer la clé API

    -OPENAI_API_KEY=MASUPERAPI

    -OPENAI_BASE_URL=MONURL