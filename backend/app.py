import streamlit as st
import pandas as pd

st.set_page_config(page_title="SAM – Search and Analysis Machine", layout="wide")
st.title("🔍 Search and Analysis Machine")

# Tabs
tab1, tab2, tab3 = st.tabs(["🔎 Пошук", "📊 Результати", "🧠 GPT-Аналіз"])

# ---------------- Пошук ----------------
with tab1:
    st.subheader("Пошук сайтів за ключовим словом")

    keyword = st.text_input("🔑 Введіть ключове слово:")
    num_results = st.slider("Скільки результатів знайти:", min_value=10, max_value=100, step=10, value=20)

    col1, col2 = st.columns(2)
    with col1:
        from_result = st.number_input("Починати з результату №", min_value=0, value=0, step=10)

    with col2:
        only_new = st.checkbox("Аналізувати лише нові сайти", value=True)

    if st.button("🚀 Запустити пошук"):
        st.info("✅ Пошук і GPT-аналіз виконуються (поки що — симуляція)")

# ---------------- Результати ----------------
with tab2:
    st.subheader("📊 Перегляд збережених результатів")
    
    # Симуляція
    demo_data = pd.DataFrame([
        {"Назва": "X-Ray Medical Ltd", "Сайт": "https://xrml.com", "Email": "info@xrml.com", "Тип": "Medical", "GPT": "Клієнт: Так"},
        {"Назва": "Industrial Scans", "Сайт": "https://ndtscan.io", "Email": "contact@ndtscan.io", "Тип": "NDT", "GPT": "Клієнт: Так"},
        {"Назва": "TechBlog", "Сайт": "https://techblog.net", "Email": "", "Тип": "Other", "GPT": "Клієнт: Ні"}
    ])
    
    show_only_yes = st.checkbox("Показати тільки перспективних (Клієнт: Так)", value=False)

    if show_only_yes:
        demo_data = demo_data[demo_data["GPT"] == "Клієнт: Так"]

    st.dataframe(demo_data)

# ---------------- GPT-Аналіз ----------------
with tab3:
    st.subheader("🧠 GPT-Аналіз нових записів")

    if st.button("🔍 Запустити аналіз (до 20 нових записів)"):
        st.warning("🔄 GPT аналіз запущено (поки що — симуляція)")
