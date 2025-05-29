import gspread
import streamlit as st
from oauth2client.service_account import ServiceAccountCredentials
from typing import List, Dict

def get_gsheet_client():
    """
    Авторизація в Google Sheets API через secrets.
    """
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(st.secrets["gcp_service_account"], scope)
    return gspread.authorize(creds)

def get_worksheet_by_name(gsheet, name: str):
    try:
        return gsheet.worksheet(name)
    except gspread.exceptions.WorksheetNotFound:
        return gsheet.add_worksheet(title=name, rows="1000", cols="20")

def read_existing_urls(sheet) -> List[str]:
    try:
        records = sheet.get_all_records()
        return [row.get("Сайт", "").strip() for row in records]
    except:
        return []

def append_rows(sheet, data: List[Dict]):
    if not data:
        return

    existing_data = sheet.get_all_values()
    if not existing_data:
        sheet.append_row(list(data[0].keys()))

    rows_to_append = [list(row.values()) for row in data]
    sheet.append_rows(rows_to_append, value_input_option="USER_ENTERED")
