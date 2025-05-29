import streamlit as st
import pandas as pd
from backend.gsheet_service import get_gsheet_client, get_worksheet_by_name

def render_companies_tab():
    st.subheader("🏢 Компанії")

    try:
        gc = get_gsheet_client()
        spreadsheet = gc.open_by_key(st.secrets["spreadsheet_id"])
        sheet = get_worksheet_by_name(spreadsheet, "результати")
        records = sheet.get_all_records()
        df = pd.DataFrame(records)

        if df.empty:
            st.info("ℹ️ У таблиці 'результати' немає даних.")
            return

        # Убираємо дублі за сайтом
        df = df.drop_duplicates(subset=["Сайт"])

        # Фільтр тільки для клієнтів з "Так"
        show_only_yes = st.checkbox("Показати тільки перспективних (Клієнт: Так)", value=True)
        if show_only_yes:
            df = df[df["GPT: Клієнт"].astype(str).str.startswith("Так")]

        # Виводимо тільки потрібні колонки
        selected_columns = ["Назва", "Сайт", "Email", "Країна", "GPT: Клієнт"]
        selected_columns = [col for col in selected_columns if col in df.columns]
        df = df[selected_columns]

        st.dataframe(df.reset_index(drop=True), use_container_width=True)

    except Exception as e:
        st.error(f"❌ Помилка при завантаженні вкладки 'результати': {e}")
