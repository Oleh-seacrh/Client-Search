import streamlit as st
import pandas as pd
from backend.gsheet_service import get_gsheet_client, get_worksheet_by_name

def render_companies_tab():
    st.subheader("🏢 Усі компанії з різних джерел")

    spreadsheet_id = st.secrets["spreadsheet_id"]
    gc = get_gsheet_client()
    sheet = gc.open_by_key(spreadsheet_id)

    all_data = []

    for tab_name in ["результати", "аналіз"]:
        try:
            ws = get_worksheet_by_name(sheet, tab_name)
            records = ws.get_all_records()
            for row in records:
                row["Джерело"] = tab_name
                all_data.append(row)
        except Exception as e:
            st.warning(f"⚠️ Не вдалося завантажити '{tab_name}': {e}")

    if not all_data:
        st.info("Немає даних для відображення.")
        return

    df = pd.DataFrame(all_data)

    # Фільтрація: лише GPT: Клієнт == Так
    if "GPT: Клієнт" in df.columns:
        df = df[df["GPT: Клієнт"] == "Так"]

    # Виводимо тільки важливі колонки
    expected_columns = ["Назва", "Сайт", "Email", "Країна", "Категорія", "Джерело"]
    missing = [col for col in expected_columns if col not in df.columns]
    for col in missing:
        df[col] = ""

    df = df[expected_columns]

    # Фільтри
    with st.expander("🔎 Фільтри"):
        col1, col2, col3 = st.columns(3)

        with col1:
            category_filter = st.multiselect("Категорія", sorted(df["Категорія"].dropna().unique()))

        with col2:
            country_filter = st.multiselect("Країна", sorted(df["Країна"].dropna().unique()))

        with col3:
            source_filter = st.multiselect("Джерело", sorted(df["Джерело"].dropna().unique()))

        if category_filter:
            df = df[df["Категорія"].isin(category_filter)]
        if country_filter:
            df = df[df["Країна"].isin(country_filter)]
        if source_filter:
            df = df[df["Джерело"].isin(source_filter)]

    st.dataframe(df.reset_index(drop=True), use_container_width=True)

