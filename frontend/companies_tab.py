import streamlit as st
import pandas as pd
from backend.gsheet_service import get_gsheet_client, get_worksheet_by_name

def render_companies_tab():
    try:
        gc = get_gsheet_client()
        sheet = gc.open_by_key(st.secrets["spreadsheet_id"])
        ws = get_worksheet_by_name(sheet, "результати")
        data = ws.get_all_records()
        df = pd.DataFrame(data)

        # Фільтруємо компанії, де GPT: Клієнт починається з "так"
        df = df[df["GPT: Клієнт"].str.strip().str.lower().str.startswith("так")]

        if df.empty:
            st.info("📭 Немає компаній, позначених GPT як 'Клієнт: Так'.")
            return

        st.markdown("### 🏢 Перспективні компанії (GPT: Клієнт = Так)")

        # Колонки для відображення
        columns_to_show = ["Назва компанії", "Сайт", "Email", "Країна", "Категорія", "Сторінка", "Висновок GPT"]
        available_columns = [col for col in columns_to_show if col in df.columns]

        st.dataframe(df[available_columns].reset_index(drop=True), use_container_width=True)

    except Exception as e:
        st.error(f"❌ Не вдалося завантажити дані з вкладки 'результати': {e}")
