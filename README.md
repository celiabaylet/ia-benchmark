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

### **Architecture :**

- `Couche bronze` : Données brutes issues du scraping : `questions_raw.csv` réalisé grâce au fichier src/ingestion/opentdb.py
Récupération des questions depuis l’API Open Trivia Database (OpenTDB)
Stockage des données brutes dans la couche Bronze
Conservation du fichier Bronze comme source non modifiée

- `Couche silver` : fichier src/enrichment/silver_clean.py + réponses de l'IA avec le fichier src/enrichment/openAI_benchmark.py (script fr/en)
    - Silver contient des observations propres et exploitables

    Suppression des valeurs invalides

    Normalisation des champs (création d'un 'QCM' pour l'IA)

    Suppression des doublons des questions

    Création d’un `question_id`

    Conversion au format Parquet


EXPLICATIONS :

    - Chaque question est transformée en QCM

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

Dans la granularité des couches Silver et Gold, on utilise l’organisation `staging`, `intermediate` et `mart` (dans une base duckdb).
Staging : première couche qui récupère et standardise les réponses du modèle, en les enrichissant avec les informations des questions.
Intermediate : couche qui prépare les indicateurs nécessaires, notamment correct_flag, qui permet d’identifier si la réponse du modèle est correcte.
Mart : couche qui répond aux questions métier en calculant les indicateurs finaux, comme le taux de réussite et le temps de réponse moyen.

### **Ingénierie des données :**

- Utilisation de dbt pour construire le lignage `staging → intermediate → gold`:
    -Générer les fichiers de documentation et le catalogue
        dbt docs generate
    -Lancer un serveur local pour visualiser le site dans votre navigateur
        dbt docs serve


### **Visualisation des résultats du benchmark :**
- **Streamlit** pour produire un dashboard interactif des résultats du benchmark

# Setup complet
- Création d’un environnement virtuel `.venv`
- Installation des dépendances depuis `requirements.txt`


- Création d’un fichier `.env` à la racine du projet
- Stockage de la clé API et de l’URL de l’API OpenAI-compatible
- Le `.env` est ajouté au `.gitignore` afin de ne pas exposer la clé API
    -OPENAI_API_KEY=MASUPERAPI
    -OPENAI_BASE_URL=MONURL