
import streamlit as st
import pandas as pd
import plotly.express as px
import json
from datetime import date
from pathlib import Path

# ==========================================
# НАСТРОЙКИ САЙТА
# ==========================================

st.set_page_config(
    page_title="Habit Tracker Dashboard",
    page_icon="📊",
    layout="wide"
)

# ==========================================
# ДИЗАЙН
# ==========================================

st.markdown("""
<style>
.block-container {
    max-width: 1100px;
    padding-top: 30px;
}

h1 {
    font-weight: 750;
}

div.stButton > button {
    border-radius: 10px;
}

div.stButton > button:hover {
    border-color: #9b7bff;
    color: #9b7bff;
}

[data-testid="stMetric"] {
    border: 1px solid #77777740;
    padding: 15px;
    border-radius: 12px;
}
</style>
""", unsafe_allow_html=True)

# ==========================================
# СОХРАНЕНИЕ ДАННЫХ
# ==========================================

DATA_FILE = Path(__file__).resolve().parent / "habits.json"

COLUMNS = ["date", "category", "minutes"]


def load_data():
    if DATA_FILE.exists():
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as file:
                data = json.load(file)

            if isinstance(data, list):
                return data

        except (OSError, json.JSONDecodeError):
            st.warning("Не вдалося прочитати JSON-файл.")

    return []


def save_data():
    with open(DATA_FILE, "w", encoding="utf-8") as file:
        json.dump(
            st.session_state.records,
            file,
            ensure_ascii=False,
            indent=4
        )


# ==========================================
# SESSION STATE
# ==========================================

if "records" not in st.session_state:
    st.session_state.records = load_data()

if "minutes" not in st.session_state:
    st.session_state.minutes = 30


# ==========================================
# КНОПКИ + И -
# ==========================================

def decrease_minutes():
    st.session_state.minutes = max(
        0,
        st.session_state.minutes - 1
    )


def increase_minutes():
    st.session_state.minutes = min(
        1440,
        st.session_state.minutes + 1
    )


# ==========================================
# ЗАГОЛОВОК
# ==========================================

st.title("📊 Habit Tracker Dashboard")

st.write(
    "Записуй свої щоденні звички, "
    "відстежуй прогрес та аналізуй результати."
)

st.divider()

# ==========================================
# ФОРМА ДОБАВЛЕНИЯ
# ==========================================

st.subheader("➕ Додати нову активність")

with st.container(border=True):

    selected_date = st.date_input(
        "📅 Дата",
        value=date.today(),
        format="YYYY/MM/DD"
    )

    category = st.selectbox(
        "📚 Категорія",
        [
            "Навчання",
            "Спорт",
            "Читання",
            "Програмування",
            "Малювання",
            "Музика",
            "Медитація",
            "Гра на інструменті"
        ]
    )

    st.write("⏱️ Скільки хвилин?")

    col1, col2, col3 = st.columns([5, 1, 1])

    with col1:
        st.number_input(
            "Хвилини",
            min_value=0,
            max_value=1440,
            key="minutes",
            label_visibility="collapsed"
        )

    with col2:
        st.button(
            "➖",
            on_click=decrease_minutes,
            use_container_width=True
        )

    with col3:
        st.button(
            "➕",
            on_click=increase_minutes,
            use_container_width=True
        )

    if st.button(
        "💾 Зберегти запис",
        type="primary"
    ):

        if st.session_state.minutes == 0:
            st.warning(
                "Будь ласка, вкажи кількість хвилин!"
            )

        else:
            new_record = {
                "date": str(selected_date),
                "category": category,
                "minutes": st.session_state.minutes
            }

            st.session_state.records.append(new_record)

            save_data()

            st.success("✅ Запис успішно збережено!")


# ==========================================
# ПЕРЕТВОРЕННЯ В PANDAS
# ==========================================

df = pd.DataFrame(
    st.session_state.records,
    columns=COLUMNS
)

if not df.empty:

    # Перетворення дати
    df["date"] = pd.to_datetime(
        df["date"],
        errors="coerce"
    )

    # Перетворення хвилин
    df["minutes"] = pd.to_numeric(
        df["minutes"],
        errors="coerce"
    ).fillna(0)

    df = df.dropna(subset=["date"])

    # ======================================
    # СТАТИСТИКА
    # ======================================

    st.divider()
    st.subheader("📈 Загальна статистика")

    total_records = len(df)
    total_minutes = int(df["minutes"].sum())
    total_hours = round(total_minutes / 60, 1)
    total_categories = df["category"].nunique()

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            "📝 Всього записів",
            total_records
        )

    with col2:
        st.metric(
            "⏱️ Всього хвилин",
            total_minutes
        )

    with col3:
        st.metric(
            "🕒 Годин",
            total_hours
        )

    with col4:
        st.metric(
            "📚 Категорій",
            total_categories
        )

    # ======================================
    # ПІДГОТОВКА ДАНИХ ДЛЯ ГРАФІКІВ
    # ======================================

    category_data = (
        df.groupby("category", as_index=False)
        ["minutes"]
        .sum()
    )

    daily_data = (
        df.groupby("date", as_index=False)
        ["minutes"]
        .sum()
        .sort_values("date")
    )

    # ======================================
    # ГРАФІК 1 - СТОВПЧИКОВИЙ
    # ======================================

    st.divider()
    st.subheader("📊 Активність за категоріями")

    fig_bar = px.bar(
        category_data,
        x="category",
        y="minutes",
        color="category",
        title="Сума хвилин за категоріями",
        labels={
            "category": "Категорія",
            "minutes": "Хвилини"
        },
        text="minutes"
    )

    fig_bar.update_layout(
        showlegend=False
    )

    st.plotly_chart(
        fig_bar,
        use_container_width=True
    )

    # ======================================
    # ГРАФІК 2 - ЛІНІЙНИЙ
    # ======================================

    st.subheader("📈 Динаміка активності по днях")

    fig_line = px.line(
        daily_data,
        x="date",
        y="minutes",
        markers=True,
        title="Щоденна активність",
        labels={
            "date": "Дата",
            "minutes": "Хвилини"
        }
    )

    st.plotly_chart(
        fig_line,
        use_container_width=True
    )

    # ======================================
    # ГРАФІК 3 - КРУГОВИЙ
    # ======================================

    st.subheader("🥧 Розподіл часу за категоріями")

    fig_pie = px.pie(
        category_data,
        names="category",
        values="minutes",
        title="Частка кожної категорії",
        hole=0.3
    )

    st.plotly_chart(
        fig_pie,
        use_container_width=True
    )

    # ======================================
    # ТАБЛИЦЯ ЗАПИСІВ
    # ======================================

    st.divider()
    st.subheader("📋 Всі записи")

    display_df = df.sort_values(
        "date",
        ascending=False
    ).copy()

    display_df["date"] = (
        display_df["date"].dt.strftime("%Y-%m-%d")
    )

    display_df = display_df.rename(
        columns={
            "date": "Дата",
            "category": "Категорія",
            "minutes": "Хвилини"
        }
    )

    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True
    )

    # ======================================
    # ОЧИЩЕННЯ ІСТОРІЇ
    # ======================================

    if st.button("🗑️ Очистити історію"):

        st.session_state.records = []

        save_data()

        st.rerun()

else:

    st.info(
        "Поки що немає записів. "
        "Додай свою першу активність!"
    )

