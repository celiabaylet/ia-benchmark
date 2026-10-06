import os
import re
import random
import time
import ast

import ollama
import pandas as pd


# ============================================================
# CONFIGURATION
# ============================================================

INPUT_PATH = "data/silver/questions_clean.parquet"
OUTPUT_PATH = "data/silver/responses.parquet"

MODEL = "llama3.1:latest"
PROMPT_VERSION = "qcm_v2"

# TEST :
# 10 = teste seulement 10 questions
# None = traite les 5097 questions
TEST_LIMIT = 30

# Sauvegarde toutes les 10 questions
CHECKPOINT_EVERY = 10


# ============================================================
# EXTRACTION DE LA LETTRE DE REPONSE
# ============================================================

def extract_letter(answer):
    """
    Extrait A, B, C ou D de la réponse du modèle.
    """

    if not answer:
        return ""

    answer = answer.strip().upper()

    # Cas idéal : le modèle répond simplement "A"
    if answer in ["A", "B", "C", "D"]:
        return answer

    # Si le modèle répond par exemple :
    # "A."
    # "Réponse : B"
    # "Je choisis C"
    match = re.search(r"\b([ABCD])\b", answer)

    if match:
        return match.group(1)

    return ""


# ============================================================
# CREATION DU QCM
# ============================================================

def create_qcm(row):
    """
    Crée les choix du QCM à partir d'une question OpenTDB.

    Pour une question multiple :
        A / B / C / D

    Pour une question boolean :
        A / B
    """

    correct_answer = str(row["correct_answer"])
    incorrect_answers = row["incorrect_answers"]

    # Le Silver contient une représentation de liste.
    if isinstance(incorrect_answers, str):
        try:
            incorrect_answers = ast.literal_eval(incorrect_answers)
        except Exception:
            incorrect_answers = []

    # Sécurité
    if not isinstance(incorrect_answers, list):
        incorrect_answers = []

    choices = [correct_answer] + incorrect_answers

    # Mélange reproductible
    random.Random(42 + int(row.name)).shuffle(choices)

    # Lettres disponibles
    letters = ["A", "B", "C", "D"]

    choices_dict = {}

    for letter, choice in zip(letters, choices):
        choices_dict[letter] = str(choice)

    # Trouver la lettre de la bonne réponse
    correct_letter = ""

    for letter, choice in choices_dict.items():
        if choice == correct_answer:
            correct_letter = letter
            break

    return choices_dict, correct_letter


# ============================================================
# CREATION DU PROMPT
# ============================================================

def build_prompt(question, choices):

    choices_text = "\n".join(
        f"{letter}. {answer}"
        for letter, answer in choices.items()
    )

    return f"""Réponds à la question suivante.

{question}

{choices_text}

Ta réponse doit être exactement une seule lettre parmi A, B, C ou D.
Ne donne aucune explication.
Ne répète pas la question.
Ne donne pas le texte de la réponse.
Réponse :"""


# ============================================================
# APPEL OLLAMA
# ============================================================

def ask_ollama(question, choices):

    prompt = build_prompt(question, choices)

    start = time.perf_counter()

    response = ollama.chat(
        model=MODEL,
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        options={
            "temperature": 0,
            "num_predict": 2
        }
    )

    elapsed = time.perf_counter() - start

    raw_answer = response["message"]["content"].strip()

    answer_letter = extract_letter(raw_answer)

    return raw_answer, answer_letter, elapsed, prompt


# ============================================================
# CHARGEMENT DU SILVER
# ============================================================

print("Chargement du Silver...")

df = pd.read_parquet(INPUT_PATH)

print(f"Questions disponibles : {len(df)}")


# ============================================================
# LIMITATION POUR LE TEST
# ============================================================

if TEST_LIMIT is not None:

    df = df.head(TEST_LIMIT).copy()

    print(f"MODE TEST : {len(df)} questions")


# ============================================================
# COLONNES DE RESULTAT
# ============================================================

df["model"] = MODEL
df["prompt_version"] = PROMPT_VERSION

df["qcm_choices"] = ""
df["correct_letter"] = ""

df["ai_answer_raw"] = ""
df["ai_answer_letter"] = ""

df["ai_correct"] = False

df["response_time"] = 0.0

df["prompt"] = ""

df["status"] = "pending"


# ============================================================
# TRAITEMENT
# ============================================================

for i, (index, row) in enumerate(df.iterrows(), start=1):

    question = row["question"]

    print()
    print("=" * 70)
    print(f"Question {i}/{len(df)}")
    print(question)

    try:

        # ----------------------------------------------------
        # Création du QCM
        # ----------------------------------------------------

        choices, correct_letter = create_qcm(row)

        print()
        print("CHOIX :")

        for letter, answer in choices.items():
            print(f"  {letter}. {answer}")

        print()
        print(f"Bonne réponse : {correct_letter}")


        # ----------------------------------------------------
        # Appel Ollama
        # ----------------------------------------------------

        raw_answer, answer_letter, response_time, prompt = ask_ollama(
            question,
            choices
        )


        # ----------------------------------------------------
        # Vérification
        # ----------------------------------------------------

        is_correct = (
            answer_letter == correct_letter
        )


        # ----------------------------------------------------
        # Sauvegarde
        # ----------------------------------------------------

        df.at[index, "qcm_choices"] = str(choices)

        df.at[index, "correct_letter"] = correct_letter

        df.at[index, "ai_answer_raw"] = raw_answer

        df.at[index, "ai_answer_letter"] = answer_letter

        df.at[index, "ai_correct"] = is_correct

        df.at[index, "response_time"] = response_time

        df.at[index, "prompt"] = prompt

        df.at[index, "status"] = "success"


        # ----------------------------------------------------
        # Affichage
        # ----------------------------------------------------

        print(f"Réponse brute IA : {raw_answer}")
        print(f"Réponse IA      : {answer_letter}")
        print(f"Bonne réponse   : {correct_letter}")
        print(f"Correct ?       : {is_correct}")
        print(f"Temps           : {response_time:.2f} secondes")


    except Exception as e:

        print(f"ERREUR : {e}")

        df.at[index, "status"] = f"error: {str(e)}"


    # ========================================================
    # CHECKPOINT
    # ========================================================

    if i % CHECKPOINT_EVERY == 0 or i == len(df):

        os.makedirs("data/silver", exist_ok=True)

        df.to_parquet(
            OUTPUT_PATH,
            index=False
        )

        print()
        print(f"Checkpoint sauvegardé : {OUTPUT_PATH}")


# ============================================================
# RESULTATS
# ============================================================

successful = df[df["status"] == "success"]

print()

print("=" * 70)
print("BENCHMARK TERMINÉ")
print("=" * 70)

print(f"Questions traitées : {len(df)}")
print(f"Réponses réussies  : {len(successful)}")


if len(successful) > 0:

    accuracy = successful["ai_correct"].mean() * 100

    avg_time = successful["response_time"].mean()

    print(f"Accuracy           : {accuracy:.2f}%")
    print(f"Temps moyen        : {avg_time:.2f} secondes")


print()

print(f"Fichier généré : {OUTPUT_PATH}")