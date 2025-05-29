import gspread
from oauth2client.service_account import ServiceAccountCredentials
from typing import List, Dict
import json
import streamlit as st

def get_gsheet_client():
    """
    Авторизація в Google Sheets API через secrets.toml
    """
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]

    creds_dict = {
        "type": st.secrets["gcp_service_account"]["type"],
        "project_id": st.secrets["gcp_service_account"]["project_id"],
        "private_key_id": st.secrets["gcp_service_account"]["private_key_id"],
        "private_key": st.secrets["gcp_service_account"]["private_key"],
        "client_email": st.secrets["gcp_service_account"]["client_email"],
        "client_id": st.secrets["gcp_service_account"]["client_id"],
        "auth_uri": st.secrets["gcp_service_account"]["auth_uri"],
        "token_uri": st.secrets["gcp_service_account"]["token_uri"],
        "auth_provider_x509_cert_url": st.secrets["gcp_service_account"]["auth_provider_x509_cert_url"],
        "client_x509_cert_url": st.secrets["gcp_service_account"]["client_x509_cert_url"],
        "universe_domain": st.secrets["gcp_service_account"]["universe_domain"]
    }

    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    return gspread.authorize(creds)

def get_worksheet_by_name(gsheet, name: str):
    """
    Повертає вкладку (worksheet) за назвою або створює її, якщо не існує.
    """
    try:
        return gsheet.worksheet(name)
    except gspread.exceptions.WorksheetNotFound:
        return gsheet.add_worksheet(title=name, rows="1000", cols="20")

def read_existing_urls(sheet) -> List[str]:
    """
    Зчитує всі вже наявні посилання з вкладки (колонка "Сайт").
    """
    try:
        records = sheet.get_all_records()
        return [row.get("Сайт", "").strip() for row in records]
    except:
        return []

def append_rows(sheet, data: List[Dict]):
    """
    Додає список словників у таблицю. Додає заголовки, якщо потрібно.
    """
    if not data:
        return

    existing_data = sheet.get_all_values()
    if not existing_data:
        sheet.append_row(list(data[0].keys()))

    rows_to_append = [list(row.values()) for row in data]
    sheet.append_rows(rows_to_append, value_input_option="USER_ENTERED")
""
