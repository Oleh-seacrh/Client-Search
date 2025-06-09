import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import streamlit as st
import pandas as pd
from backend.search_logic import perform_search_and_analysis
from backend.gsheet_service import get_gsheet_client, get_worksheet_by_name
from frontend.companies_tab import render_companies_tab
from frontend.search_tab import render_search_tab



st.set_page_config(page_title="SAM – Search and Analysis Machine", layout="wide")
st.title("🔍 Search and Analysis Machine")

gsheet_id = st.secrets["spreadsheet_id"]


tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["🔎 Пошук", "📊 Результати", "🧠 GPT-Аналіз", "📇 CRM", "🏢 Компанії", "📇 Client"])


with tab1:
    
    st.subheader("Пошук сайтів за ключовим словом")

    keyword = st.text_input("🔑 Введіть ключове слово:")
    num_results = st.slider("Скільки результатів знайти:", min_value=10, max_value=100, step=10, value=20)

    col1, col2 = st.columns(2)
    with col1:
        from_result = st.number_input("Починати з результату №", min_value=0, value=0, step=10)

    with col2:
        only_new = st.checkbox("Аналізувати лише нові сайти", value=True)

    if st.button("🔍 Почати пошук сайтів", key="start_site_search") and keyword:
        with st.spinner("🔍 Виконується пошук і аналіз..."):
            gc = get_gsheet_client()
            results = perform_search_and_analysis(keyword, gc, gsheet_id, only_new, num_results, from_result)
            st.success(f"✅ Збережено {len(results)} нових записів.")
    st.info("🔒 Пошук тимчасово відключено")


with tab2:
    st.subheader("📊 Перегляд збережених результатів")

    try:
        gc = get_gsheet_client()
        sheet = gc.open_by_key(gsheet_id)
        ws = get_worksheet_by_name(sheet, "результати")
        data = ws.get_all_records()
        df = pd.DataFrame(data)

        show_only_yes = st.checkbox("Показати тільки перспективних (Клієнт: Так)", value=False)

        if show_only_yes:
            df = df[df["GPT: Клієнт"] == "Так"]

        st.dataframe(df)

    except Exception as e:
        st.error(f"❌ Не вдалося завантажити дані: {e}")



with tab3:
    st.subheader("🧠 GPT-Аналіз нових записів")

    if st.button("🔍 Запустити аналіз (до 20 нових записів)", key="analyze_results_from_companies"):
        st.warning("🔄 GPT аналіз запущено (поки що — симуляція)")


with tab4:
    render_search_tab()
with tab5:
    render_companies_tab()
with tab6:
    st.subheader("📇 Дані CRM (вкладка 'Client')")

    try:
        gc = get_gsheet_client()
        sheet = gc.open_by_key(st.secrets["spreadsheet_id"])
        ws = sheet.worksheet("Client")
        data = ws.get_all_records()
        df = pd.DataFrame(data)

        if df.empty:
            st.info("Таблиця порожня 🕳️")
        else:
            st.dataframe(df)
    except Exception as e:
        st.error(f"Помилка: {e}")

