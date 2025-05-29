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

        # Всі необхідні колонки (без "Сторінка")
        required_columns = ["Компанія", "Сайт", "Email", "Країна", "Категорія", "Висновок GPT"]

        # Додаємо порожні колонки, якщо їх не вистачає
        for col in required_columns:
            if col not in df.columns:
                df[col] = ""

        # Переупорядковуємо колонки
        df = df[required_columns]

        # Видаляємо дублікати за сайтом (ігноруємо регістр і пробіли)
        df["Сайт_normalized"] = df["Сайт"].str.strip().str.lower()
        df = df.drop_duplicates(subset="Сайт_normalized", keep="first")
        df = df.drop(columns=["Сайт_normalized"])

        st.markdown("### 🏢 Перспективні компанії (GPT: Клієнт = Так)")

        if df.empty:
            st.info("📭 Немає компаній, позначених GPT як 'Клієнт: Так'. Але структура таблиці збережена.")
        else:
            st.dataframe(df.reset_index(drop=True), use_container_width=True)

    except Exception as e:
        st.error(f"❌ Не вдалося завантажити дані з вкладки 'результати': {e}")
