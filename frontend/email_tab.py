import streamlit as st
import pandas as pd
from backend.gsheet_service import get_gsheet_client, get_or_create_worksheet
from backend.email_extractor import extract_emails_from_gmail  # Це створимо пізніше

def render_email_tab():
    st.subheader("📧 Перевірка нових листів з вкладки 'Email' у пошті")

    if st.button("🔍 Перевірити пошту та витягнути контакти"):
        with st.spinner("Зчитування листів з Gmail..."):
            results = extract_emails_from_gmail()  # Повертає список словників

            if not results:
                st.info("Немає нових клієнтських листів.")
                return

            # Підключення до Google Sheets
            gc = get_gsheet_client()
            sh = gc.open_by_key(st.secrets["spreadsheet_id"])
            ws = get_or_create_worksheet(sh, "Email")

            # Отримуємо існуючі дані, щоб уникнути дублів
            existing_data = ws.get_all_records()
            existing_emails = {row['Email'] for row in existing_data if 'Email' in row}

            # Додаємо лише нові
            new_rows = []
            for row in results:
                if row["Email"] not in existing_emails:
                    new_rows.append([
                        row.get("Email", ""),
                        row.get("Сайт", ""),
                        row.get("Телефон", ""),
                        row.get("Бренд", ""),
                        row.get("Продукт", ""),
                        row.get("Кількість", ""),
                        row.get("Хто звернувся", ""),
                        row.get("Повний текст", ""),
                    ])

            if new_rows:
                ws.append_rows(new_rows)
                st.success(f"Додано {len(new_rows)} нових контактів.")
            else:
                st.info("Усі контакти вже присутні у таблиці.")

            # Виводимо в таблиці на екрані
            df = pd.DataFrame(new_rows, columns=[
                "Email", "Сайт", "Телефон", "Бренд", "Продукт", "Кількість", "Хто звернувся", "Повний текст"
            ])
            st.dataframe(df)
