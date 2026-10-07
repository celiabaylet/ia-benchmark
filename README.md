# Projet Trivial Poursuite
** méthodologie, votre organisation de projet et le setup complet**



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

- `Couche bronze` : Données brutes issues du scraping : `questions_raw.csv`
- `Couche silver` : Données pré-traitées (nettoyage, normalisation, etc.) +  réponses brutes + nettoyé du modèle `en parquet`
    - Silver contient des observations propres et exploitables
- `Couche gold` : Données métiers (performance des modèles, performance des prompts, etc.) `format duckdb`
    - Gold répond directement à une question métier

Dans la granularité des couches Silver et Gold, on utilise l’organisation `stating`, `intermediate` et `mart` (dans une base duckdb).

### **Ingénierie des données :**

- Utilisation de dbt pour construire le lignage `staging → intermediate → gold`.

### **Visualisation des résultats du benchmark :**

- Utilisez **Streamlit** pour produire un dashboard interactif des résultats du benchmark

# Setup complet
ajouter un .venv
serveur + clé api pour utiliser openAI
fichier requirements + pandas + requests
dbt
duckdb 
streamlit
AJOUTER une clé API dans un .env pour lancer 'openAI_benchmark'
