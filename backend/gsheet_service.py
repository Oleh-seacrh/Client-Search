import gspread
from oauth2client.service_account import ServiceAccountCredentials
from typing import List, Dict
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

    creds_dict = st.secrets["gcp_service_account"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    return gspread.authorize(creds)


def get_worksheet_by_name(gsheet, name: str):
    """
    Повертає вкладку за назвою або створює її.
    """
    try:
        return gsheet.worksheet(name)
    except gspread.exceptions.WorksheetNotFound:
        return gsheet.add_worksheet(title=name, rows="1000", cols="20")


def read_existing_websites(sheet) -> List[str]:
    """
    Зчитує всі вже наявні Website з вкладки (колонка 'Website').
    """
    try:
        records = sheet.get_all_records()
        return [row.get("Website", "").strip().lower() for row in records if row.get("Website")]
    except Exception as e:
        print("Error reading websites:", e)
        return []


def append_rows(sheet, data: List[Dict]):
    """
    Додає список словників у таблицю. Додає заголовки, якщо потрібно.
    """
    if not data:
        return

    existing_data = sheet.get_all_values()
    headers = sheet.row_values(1) if existing_data else []

    # If no headers, write them
    if not headers:
        headers = list(data[0].keys())
        sheet.append_row(headers)

    # Ensure all rows have all columns in order
    rows_to_append = []
    for row in data:
        full_row = [row.get(h, "") for h in headers]
        rows_to_append.append(full_row)

    sheet.append_rows(rows_to_append, value_input_option="USER_ENTERED")


def update_or_append_rows(sheet, data: List[Dict], key_column: str = "Website"):
    """
    Оновлює рядки за ключовою колонкою, або додає нові.
    """
    existing_records = sheet.get_all_records()
    existing_keys = [row.get(key_column, "").strip().lower() for row in existing_records]
    headers = sheet.row_values(1)

    updates = 0
    new_data = []

    for row in data:
        row_key = row.get(key_column, "").strip().lower()
        if row_key in existing_keys:
            index = existing_keys.index(row_key) + 2  # headers + 1-indexed
            full_row = [row.get(h, "") for h in headers]
            sheet.update(f"A{index}:{chr(65+len(full_row)-1)}{index}", [full_row])
            updates += 1
        else:
            new_data.append(row)

    if new_data:
        append_rows(sheet, new_data)

    print(f"Updated: {updates}, Added new: {len(new_data)}")
