import os
import re
import random
import time
import ast
import pandas as pd
from openai import OpenAI
from dotenv import load_dotenv


# ============================================================
# CONFIGURATION
# ============================================================

INPUT_PATH = "data/silver/questions_clean.parquet"
OUTPUT_PATH = "data/silver/responses.parquet"

MODEL = "granite-4.2"

PROMPTS = {
    "qcm_fr": "français",
    "qcm_en": "anglais"
}

# TEST :
# 10 = teste seulement 10 questions
# None = traite les 5097 questions
TEST_LIMIT = 5300

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

def build_prompt(question, choices, prompt_version):

    choices_text = "\n".join(
        f"{letter}. {answer}"
        for letter, answer in choices.items()
    )

    if prompt_version == "qcm_fr":

        return f"""Réponds à la question suivante.

{question}

{choices_text}

Ta réponse doit être exactement une seule lettre parmi A, B, C ou D.

Ne donne aucune explication.
Ne répète pas la question.
Ne donne pas le texte de la réponse.

Réponse :"""

    elif prompt_version == "qcm_en":

        return f"""Answer the following question.

{question}

{choices_text}

Your answer must be exactly one letter: A, B, C, or D.

Do not provide any explanation.
Do not repeat the question.
Do not provide the answer text.

Answer:"""

    else:
        raise ValueError(f"Prompt inconnu : {prompt_version}")


# ============================================================
# APPEL openAI
# ============================================================

load_dotenv()

client = OpenAI(
    base_url=os.getenv("OPENAI_BASE_URL"),
    api_key=os.getenv("OPENAI_API_KEY")
)


def ask_model(question, choices, prompt_version):

    prompt = build_prompt(
        question,
        choices,
        prompt_version
    )

    start = time.perf_counter()

    response = client.chat.completions.create(
        model="granite-4.2",
        messages=[
            {"role": "user", "content": prompt}
        ],
        temperature=0,
        max_tokens=5,
        reasoning_effort='none'
    )


    elapsed = time.perf_counter() - start

    raw_answer = (response.choices[0].message.content or "").strip()
    answer_letter = extract_letter(raw_answer)

    return raw_answer, answer_letter, elapsed, prompt


# ============================================================
# CHARGEMENT DU SILVER
# ============================================================

print("Chargement du Silver...")

df = pd.read_parquet(INPUT_PATH)

if TEST_LIMIT is not None:
    df = df.head(TEST_LIMIT).copy()


# ============================================================
# BENCHMARK
# ============================================================

results = []

for i, (index, row) in enumerate(df.iterrows(), start=1):

    question = row["question"]

    try:

        # Création du QCM UNE SEULE FOIS
        # pour que les prompts français et anglais
        # reçoivent exactement les mêmes choix.

        choices, correct_letter = create_qcm(row)

        # On teste les deux prompts
        for prompt_version in PROMPTS:

            raw_answer, answer_letter, response_time, prompt = ask_model(
                question,
                choices,
                prompt_version
            )

            is_correct = answer_letter == correct_letter

            results.append({
                "question_id": row["question_id"],
                "ai_answer_raw": raw_answer,
                "ai_answer_letter": answer_letter,
                "correct_letter": correct_letter,
                "ai_correct": is_correct,
                "response_time": response_time,
                "model": MODEL,
                "prompt_version": prompt_version,
                "status": "success"
            })

            print(
                f"Question {i}/{len(df)} | "
                f"Prompt: {prompt_version} | "
                f"Réponse: {answer_letter} | "
                f"Correcte: {is_correct} | "
                f"Temps: {response_time:.2f}s"
            )

    except Exception as e:

        print(
            f"Question {i}/{len(df)} | ERREUR: {str(e)}"
        )

    # ========================================================
    # CHECKPOINT
    # ========================================================

    if i % CHECKPOINT_EVERY == 0 or i == len(df):

        results_df = pd.DataFrame(results)

        os.makedirs("data/silver", exist_ok=True)

        results_df.to_parquet(
            OUTPUT_PATH,
            index=False
        )

        print(
            f"Checkpoint sauvegardé : "
            f"{i}/{len(df)} questions"
        )


# ============================================================
# SAUVEGARDE FINALE
# ============================================================

results_df = pd.DataFrame(results)

results_df.to_parquet(
    OUTPUT_PATH,
    index=False
)


# ============================================================
# RESULTATS
# ============================================================

successful = results_df[
    results_df["status"] == "success"
]

if len(successful) > 0:

    accuracy = successful["ai_correct"].mean() * 100

    avg_time = successful["response_time"].mean()

    print()

    print("BENCHMARK TERMINÉ")

    print(f"Questions testées : {len(df)}")

    print(f"Réponses réussies : {len(successful)}")

    print(f"Accuracy globale : {accuracy:.2f}%")

    print(f"Temps moyen : {avg_time:.2f} sec/question")

    print(f"Fichier : {OUTPUT_PATH}")