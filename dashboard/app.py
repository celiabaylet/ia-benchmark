import streamlit as st
import duckdb
import pandas as pd


# ============================================================
# CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Trivial Pursuit",
    layout="wide"
)

DB_PATH = "warehouse/trivial.duckdb"


# ============================================================
# CONNEXION DUCKDB
# ============================================================

@st.cache_resource
def get_connection():
    return duckdb.connect(DB_PATH, read_only=True)


con = get_connection()


# ============================================================
# CHARGEMENT DES MARTS GOLD
# ============================================================

@st.cache_data
def load_category():
    return con.execute("""
        SELECT
            category,
            total_questions,
            correct_answers,
            accuracy_percent,
            avg_response_time
        FROM main_gold.mart_category_performance
        ORDER BY accuracy_percent DESC
    """).fetchdf()


@st.cache_data
def load_difficulty():
    return con.execute("""
        SELECT
            difficulty,
            total_questions,
            correct_answers,
            accuracy_percent,
            avg_response_time
        FROM main_gold.mart_difficulty_performance
    """).fetchdf()


@st.cache_data
def load_prompt():
    return con.execute("""
        SELECT
            prompt_version,
            total_questions,
            correct_answers,
            accuracy_percent,
            avg_response_time
        FROM main_gold.mart_prompt_performance
    """).fetchdf()


@st.cache_data
def load_type():
    return con.execute("""
        SELECT
            type,
            total_questions,
            correct_answers,
            accuracy_percent,
            avg_response_time
        FROM main_gold.mart_type_performance
    """).fetchdf()


df_category = load_category()
df_difficulty = load_difficulty()
df_prompt = load_prompt()
df_type = load_type()


# ============================================================
# TITRE
# ============================================================

st.title("Benchmark du modèle Granite 4.2")
st.markdown(
    """
    Analyse des performances du modèle sur les questions de
    **Trivial Pursuit**, selon la catégorie, la difficulté,
    le type de question et la langue du prompt.
    """
)

st.divider()


# ============================================================
# KPI GLOBAUX
# ============================================================

total_questions = int(
    df_category["total_questions"].sum()
)

total_correct = int(
    df_category["correct_answers"].sum()
)

global_accuracy = (
    total_correct / total_questions * 100
    if total_questions > 0
    else 0
)

global_time = (
    (
        df_category["avg_response_time"]
        * df_category["total_questions"]
    ).sum()
    / total_questions
    if total_questions > 0
    else 0
)

col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        "Questions évaluées",
        f"{total_questions:,}".replace(",", " ")
    )

with col2:
    st.metric(
        "Taux de réussite global",
        f"{global_accuracy:.2f} %"
    )

with col3:
    st.metric(
        "Temps moyen",
        f"{global_time:.2f} s"
    )


st.divider()


# ============================================================
# QUESTION 1
# ============================================================

st.header("1️ Dans quelles catégories le modèle est-il le plus performant ?")

st.markdown(
    """
    **Objectif :** comparer le taux de bonnes réponses selon
    les différentes catégories de questions.
    """
)

# Graphique accuracy par catégorie
st.bar_chart(
    df_category.set_index("category")["accuracy_percent"],
    y_label="Taux de bonnes réponses (%)",
    x_label="Catégorie"
)

st.markdown("### Résultats par catégorie")

st.dataframe(
    df_category[
        [
            "category",
            "total_questions",
            "correct_answers",
            "accuracy_percent",
            "avg_response_time"
        ]
    ],
    use_container_width=True,
    hide_index=True
)

best_category = df_category.iloc[0]

st.divider()


# ============================================================
# QUESTION 2
# ============================================================

st.header(
    "2️ La difficulté influence-t-elle les performances et le temps de réponse ?"
)

st.markdown(
    """
    **Objectif :** comparer à la fois le taux de bonnes réponses
    et le temps de réponse moyen selon le niveau de difficulté.
    """
)

# Ordre logique des difficultés
difficulty_order = ["easy", "medium", "hard"]

df_difficulty["difficulty"] = pd.Categorical(
    df_difficulty["difficulty"],
    categories=difficulty_order,
    ordered=True
)

df_difficulty = df_difficulty.sort_values("difficulty")

# Traduction pour l'affichage
difficulty_labels = {
    "easy": "Facile",
    "medium": "Moyen",
    "hard": "Difficile"
}

df_difficulty["difficulty_label"] = (
    df_difficulty["difficulty"]
    .astype(str)
    .map(difficulty_labels)
)


col1, col2 = st.columns(2)

with col1:
    st.markdown("### Taux de réussite selon la difficulté")

    st.bar_chart(
        df_difficulty.set_index("difficulty_label")[
            "accuracy_percent"
        ],
        y_label="Taux de réussite (%)",
        x_label="Difficulté"
    )

with col2:
    st.markdown("### Temps de réponse selon la difficulté")

    st.bar_chart(
        df_difficulty.set_index("difficulty_label")[
            "avg_response_time"
        ],
        y_label="Temps moyen (secondes)",
        x_label="Difficulté"
    )

st.markdown("### Résultats par difficulté")

st.dataframe(
    df_difficulty[
        [
            "difficulty_label",
            "total_questions",
            "correct_answers",
            "accuracy_percent",
            "avg_response_time"
        ]
    ],
    use_container_width=True,
    hide_index=True
)


st.divider()


# ============================================================
# QUESTION 3
# ============================================================

st.header(
    "3️ Le type de question influence-t-il les performances ?"
)

st.markdown(
    """
    **Objectif :** comparer les performances et le temps de réponse
    entre les questions **Boolean** et **Multiple Choice**.
    """
)

# Traduction des types
type_labels = {
    "boolean": "Boolean",
    "multiple": "Multiple Choice"
}

df_type["type_label"] = (
    df_type["type"]
    .astype(str)
    .str.lower()
    .map(type_labels)
    .fillna(df_type["type"])
)

col1, col2 = st.columns(2)

with col1:
    st.markdown("### Taux de réussite selon le type")

    st.bar_chart(
        df_type.set_index("type_label")[
            "accuracy_percent"
        ],
        y_label="Taux de réussite (%)",
        x_label="Type de question"
    )

with col2:
    st.markdown("### Temps de réponse selon le type")

    st.bar_chart(
        df_type.set_index("type_label")[
            "avg_response_time"
        ],
        y_label="Temps moyen (secondes)",
        x_label="Type de question"
    )

st.markdown("### Résultats par type de question")

st.dataframe(
    df_type[
        [
            "type_label",
            "total_questions",
            "correct_answers",
            "accuracy_percent",
            "avg_response_time"
        ]
    ],
    use_container_width=True,
    hide_index=True
)


st.divider()


# ============================================================
# QUESTION 4
# ============================================================

st.header(
    "4️ Le langage du prompt influence-t-il les performances ?"
)

st.markdown(
    """
    **Objectif :** comparer le taux de bonnes réponses et le temps
    de réponse moyen entre les prompts en français et en anglais.
    """
)

# Traduction des prompts
prompt_labels = {
    "qcm_fr": "Français",
    "qcm_en": "Anglais"
}

df_prompt["language"] = (
    df_prompt["prompt_version"]
    .map(prompt_labels)
    .fillna(df_prompt["prompt_version"])
)

col1, col2 = st.columns(2)

with col1:
    st.markdown("### Taux de réussite selon la langue du prompt")

    st.bar_chart(
        df_prompt.set_index("language")[
            "accuracy_percent"
        ],
        y_label="Taux de réussite (%)",
        x_label="Langue du prompt"
    )

with col2:
    st.markdown("### Temps de réponse selon la langue")

    st.bar_chart(
        df_prompt.set_index("language")[
            "avg_response_time"
        ],
        y_label="Temps moyen (secondes)",
        x_label="Langue du prompt"
    )

st.markdown("### Comparaison Français / Anglais")

st.dataframe(
    df_prompt[
        [
            "language",
            "total_questions",
            "correct_answers",
            "accuracy_percent",
            "avg_response_time"
        ]
    ],
    use_container_width=True,
    hide_index=True
)


# ============================================================
# CONCLUSION AUTOMATIQUE
# ============================================================

st.divider()


st.header(" Synthèse")

# Meilleure catégorie en taux de réussite
best_category = df_category.loc[
    df_category["accuracy_percent"].idxmax()
]

# Difficulté avec meilleure accuracy
best_difficulty = df_difficulty.loc[
    df_difficulty["accuracy_percent"].idxmax()
]

# Difficulté avec le temps de réponse moyen le plus faible
best_difficulty_time = df_difficulty.loc[
    df_difficulty["avg_response_time"].idxmin()
]

# Type avec meilleure accuracy
best_type = df_type.loc[
    df_type["accuracy_percent"].idxmax()
]

# Type avec le temps de réponse moyen le plus faible
best_type_time = df_type.loc[
    df_type["avg_response_time"].idxmin()
]

# Prompt avec meilleure accuracy
best_prompt = df_prompt.loc[
    df_prompt["accuracy_percent"].idxmax()
]

# Prompt avec le temps de réponse moyen le plus faible
best_prompt_time = df_prompt.loc[
    df_prompt["avg_response_time"].idxmin()
]

st.markdown(
    f"""
    - **Meilleure catégorie en taux de réussite :** {best_category['category']}
      ({best_category['accuracy_percent']:.2f} %)

    - **Difficulté :** meilleur taux de réussite = {best_difficulty['difficulty_label']}
      ({best_difficulty['accuracy_percent']:.2f} %) ;
      temps de réponse moyen le plus faible = {best_difficulty_time['difficulty_label']}
      ({best_difficulty_time['avg_response_time']:.2f} s)

    - **Type de question :** meilleur taux de réussite = {best_type['type_label']}
      ({best_type['accuracy_percent']:.2f} %) ;
      temps de réponse moyen le plus faible = {best_type_time['type_label']}
      ({best_type_time['avg_response_time']:.2f} s)

    - **Prompt :** meilleur taux de réussite = {best_prompt['language']}
      ({best_prompt['accuracy_percent']:.2f} %) ;
      temps de réponse moyen le plus faible = {best_prompt_time['language']}
      ({best_prompt_time['avg_response_time']:.2f} s)
    """
)

st.caption(
    "Données issues des modèles Gold générés avec dbt à partir du benchmark Granite 4.2."
)