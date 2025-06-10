import streamlit as st
import pandas as pd
from backend.gsheet_service import get_gsheet_client, get_worksheet_by_name


def render_companies_tab():
    try:
        gc = get_gsheet_client()
        sheet = gc.open_by_key(st.secrets["spreadsheet_id"])
        ws = get_worksheet_by_name(sheet, "Client")
        data = ws.get_all_records()
        df = pd.DataFrame(data)

        df["Source"] = df.get("Source", "table")

        # Фільтрація компаній, які GPT позначив як Client: Yes
        df = df[df["Client"].str.strip().str.lower() == "yes"]

        # Обов’язкові колонки
        required_columns = ["Company", "Website", "Email", "Country", "Category", "Source"]

        # Додаємо порожні колонки, якщо відсутні
        for col in required_columns:
            if col not in df.columns:
                df[col] = ""

        # Упорядковуємо колонки
        df = df[required_columns]

        # Видаляємо дублікати за Website
        df["Website_normalized"] = df["Website"].str.strip().str.lower()
        df = df.drop_duplicates(subset="Website_normalized", keep="first")
        df = df.drop(columns=["Website_normalized"])

        st.markdown("### 🏢 Potential Clients (Client = Yes)")

        if df.empty:
            st.info("📭 No companies marked as 'Client: Yes'. Table structure is preserved.")
        else:
            st.dataframe(df.reset_index(drop=True), use_container_width=True)

    except Exception as e:
        st.error(f"❌ Failed to load data from 'Client' tab: {e}")
