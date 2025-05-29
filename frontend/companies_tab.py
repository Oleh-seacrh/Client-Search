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

        # Фільтруємо тільки компанії, позначені GPT як потенційні клієнти
        df = df[df["GPT: Клієнт"].str.strip().str.lower().str.startswith("так")]


        if df.empty:
            st.info("📭 Немає компаній, позначених GPT як 'Клієнт: Так'.")
            return

        st.markdown("### 🏢 Перспективні компанії (GPT: Клієнт = Так)")

        # Вибрані колонки для відображення (з перевіркою наявності)
        columns_to_show = [col for col in [
    "Компанія", "Сайт", "Email", "Категорія", "Країна", "GPT: Коментар"
] if col in df.columns]

        st.dataframe(df[columns_to_show].reset_index(drop=True), use_container_width=True)

    except Exception as e:
        st.error(f"❌ Не вдалося завантажити дані з вкладки 'результати': {e}")
