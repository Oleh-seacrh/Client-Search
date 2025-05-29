import streamlit as st
import gspread
from utils import get_gsheet_client


def render_companies_tab():
    st.header("📋 Список компаній")

    # Отримуємо доступ до Google Sheets
    gc = get_gsheet_client()
    spreadsheet_id = st.secrets["spreadsheet_id"]
    spreadsheet = gc.open_by_key(spreadsheet_id)

    try:
        sheet = spreadsheet.worksheet("Компанії")
    except gspread.exceptions.WorksheetNotFound:
        st.warning("Не знайдено вкладку 'Компанії'.")
        return

    # Отримуємо всі значення
    data = sheet.get_all_values()
    if not data or len(data) < 2:
        st.info("Поки що немає компаній для відображення.")
        return

    # Витягуємо заголовки та дані
    headers = data[0]
    rows = data[1:]

    # Перетворюємо в список словників для зручності
    structured_data = [dict(zip(headers, row)) for row in rows]

    # Сортуємо за алфавітом
    structured_data.sort(key=lambda x: x.get("Назва компанії", "").lower())

    # Виводимо таблицю
    st.dataframe(structured_data, use_container_width=True)

