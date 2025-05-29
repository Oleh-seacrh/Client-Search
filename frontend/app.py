import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import streamlit as st
import pandas as pd
# from backend.search_logic import perform_search_and_analysis
# from backend.gsheet_service import get_gsheet_client, get_worksheet_by_name
# from frontend.companies_tab import render_companies_tab

st.set_page_config(page_title="SAM – Search and Analysis Machine", layout="wide")
st.title("🔍 Search and Analysis Machine")

# gsheet_id = st.secrets["spreadsheet_id"]

# Tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs(["🔎 Пошук", "📊 Результати", "🧠 GPT-Аналіз", "📇 CRM", "🏢 Компанії"])

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

    # if st.button("🚀 Запустити пошук") and keyword:
    #     with st.spinner("🔍 Виконується пошук і аналіз..."):
    #         gc = get_gsheet_client()
    #         results = perform_search_and_analysis(keyword, gc, gsheet_id, only_new, num_results, from_result)
    #         st.success(f"✅ Збережено {len(results)} нових записів.")
    st.info("🔒 Пошук тимчасово відключено")

# ---------------- Результати ----------------
with tab2:
    st.subheader("📊 Перегляд збережених результатів")
    # try:
    #     gc = get_gsheet_client()
    #     sheet = gc.open_by_key(gsheet_id)
    #     ws = get_worksheet_by_name(sheet, "результати")
    #     data = ws.get_all_records()
    #     df = pd.DataFrame(data)

    #     show_only_yes = st.checkbox("Показати тільки перспективних (Клієнт: Так)", value=False)

    #     if show_only_yes:
    #         df = df[df["GPT: Клієнт"] == "Так"]

    #     st.dataframe(df)
    # except Exception as e:
    #     st.error(f"❌ Не вдалося завантажити дані: {e}")
    st.info("🔒 Підключення до Google Sheets тимчасово вимкнене")

# ---------------- GPT-Аналіз ----------------
with tab3:
    st.subheader("🧠 GPT-Аналіз нових записів")

    if st.button("🔍 Запустити аналіз (до 20 нових записів)"):
        st.warning("🔄 GPT аналіз запущено (поки що — симуляція)")

# ---------------- CRM ----------------
with tab4:
    st.subheader("📇 Потенційні клієнти (CRM)")
    # try:
    #     gc = get_gsheet_client()
    #     sheet = gc.open_by_key(gsheet_id)
    #     ws = get_worksheet_by_name(sheet, "результати")
    #     data = ws.get_all_records()
    #     df = pd.DataFrame(data)

    #     if not df.empty:
    #         df = df[df["GPT: Клієнт"] == "Так"]

    #         category_filter = st.multiselect("Категорія:", sorted(df["Категорія"].dropna().unique()))
    #         country_filter = st.multiselect("Країна:", sorted(df["Країна"].dropna().unique()))

    #         if category_filter:
    #             df = df[df["Категорія"].isin(category_filter)]

    #         if country_filter:
    #             df = df[df["Країна"].isin(country_filter)]

    #         st.dataframe(df.reset_index(drop=True), use_container_width=True)
    #     else:
    #         st.info("Немає даних для відображення.")
    # except Exception as e:
    #     st.error(f"❌ Не вдалося завантажити клієнтів: {e}")
    st.info("🔒 CRM тимчасово відключено")

# ---------------- Компанії ----------------
with tab5:
    # render_companies_tab()
    st.info("🔒 Вкладка 'Компанії' тимчасово вимкнена")
    import gspread
from oauth2client.service_account import ServiceAccountCredentials

st.subheader("🧪 Тест з'єднання з Google Sheets")

if st.button("🔍 Перевірити доступ"):
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        credentials = ServiceAccountCredentials.from_json_keyfile_dict(
            st.secrets["gcp_service_account"], scope
        )

        gc = gspread.authorize(credentials)
        sheet = gc.open_by_key(st.secrets["spreadsheet_id"])
        worksheet = sheet.sheet1
        st.success("✅ З'єднання успішне! Ось перші рядки:")
        st.write(worksheet.get_all_records()[:5])

    except Exception as e:
        st.error(f"❌ Помилка: {e}")
