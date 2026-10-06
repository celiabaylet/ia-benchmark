import pandas as pd
import hashlib
import os


# =========================================================
# Configuration
# =========================================================

INPUT_PATH = "data/bronze/questions_raw.csv"
OUTPUT_PATH = "data/silver/questions_clean.parquet"


# =========================================================
# Création du dossier Silver
# =========================================================

os.makedirs("data/silver", exist_ok=True)


# =========================================================
# 1. Chargement Bronze
# =========================================================

print("Chargement du Bronze...")

df = pd.read_csv(INPUT_PATH)

print(f"Questions chargées : {len(df)}")


# =========================================================
# 2. Suppression des lignes invalides
# =========================================================

df = df.dropna(
    subset=[
        "category",
        "difficulty",
        "question",
        "correct_answer",
        "type"
    ]
).copy()

print(
    f"Après suppression des lignes invalides : {len(df)}"
)


# =========================================================
# 3. Nettoyage des textes
# =========================================================

df["question"] = (
    df["question"]
    .astype(str)
    .str.strip()
)

df["correct_answer"] = (
    df["correct_answer"]
    .astype(str)
    .str.strip()
)

df["category"] = (
    df["category"]
    .astype(str)
    .str.strip()
)

df["difficulty"] = (
    df["difficulty"]
    .astype(str)
    .str.strip()
    .str.lower()
)

df["type"] = (
    df["type"]
    .astype(str)
    .str.strip()
    .str.lower()
)


# =========================================================
# 4. Création d'un identifiant unique
# =========================================================

def create_question_id(question):

    return hashlib.sha256(
        question.lower().strip().encode("utf-8")
    ).hexdigest()[:16]


df["question_id"] = df["question"].apply(
    create_question_id
)


# =========================================================
# 5. Suppression des doublons
# =========================================================

before = len(df)

df = df.drop_duplicates(
    subset=["question_id"]
).copy()

after = len(df)

print(
    f"Doublons supprimés : {before - after}"
)

print(
    f"Questions uniques : {after}"
)


# =========================================================
# 6. Réorganisation des colonnes
# =========================================================

df = df[
    [
        "question_id",
        "category",
        "type",
        "difficulty",
        "question",
        "correct_answer",
        "incorrect_answers"
    ]
]


# =========================================================
# 7. Sauvegarde Silver
# =========================================================

df.to_parquet(
    OUTPUT_PATH,
    index=False
)


# =========================================================
# 8. Résumé
# =========================================================

print()
print("==========================================")
print("SILVER CLEAN TERMINÉE")
print("==========================================")

print(
    f"Questions finales : {len(df)}"
)

print(
    f"Fichier : {OUTPUT_PATH}"
)

print()
print("Répartition par difficulté :")

print(
    df["difficulty"].value_counts()
)

print()
print("Répartition par type :")

print(
    df["type"].value_counts()
)

print()
print("Nombre de catégories :")

print(
    df["category"].nunique()
)

print("==========================================")