from backend.gsheet_service import get_gsheet_client
import re
import streamlit as st
import pandas as pd

def load_companies_from_tab(source_tab: str, spreadsheet_id: str):
    gc = get_gsheet_client()
    sh = gc.open_by_key(spreadsheet_id)

    # Отримуємо дані з джерела
    ws = sh.worksheet(source_tab)
    data = ws.col_values(1)[1:]  # Пропускаємо заголовок

    # Працюємо тепер тільки з вкладкою "Client"
    try:
        ws_client = sh.worksheet("Client")
        existing = set(name.strip().upper() for name in ws_client.col_values(1)[1:])  # Перевірка по Company
    except:
        ws_client = sh.add_worksheet(title="Client", rows="1000", cols="20")
        ws_client.update("A1", [["Company"]])
        existing = set()

    log_output = []
    new_entries = []

    for name in data:
        if not name:
            continue
        original = name
        name = name.strip().lower()

        # Видаляємо префікси
        for prefix in ["фоп", "тов", "пп"]:
            if name.startswith(prefix):
                name = name[len(prefix):].strip()

        name = name.replace("«", "").replace("»", "").replace("\"", "")
        name = ' '.join(name.split())
        cleaned = name.upper()

        if len(cleaned) > 2 and cleaned not in existing and cleaned not in [x[0] for x in new_entries]:
            new_entries.append([cleaned])
            log_output.append(f"➕ Added: {cleaned}")
        else:
            log_output.append(f"🔁 Skipped duplicate: {original}")

    # Додаємо нові записи
    if new_entries:
        next_row = len(existing) + 2
        ws_client.update(f"A{next_row}:A{next_row + len(new_entries) - 1}", new_entries)

    return log_output, len(new_entries)


def get_new_clients_from_tab(tab_name: str):
    gc = get_gsheet_client()
    sh = gc.open_by_key(st.secrets["spreadsheet_id"])

    # Джерело
    source_map = {
        "Аналіз": "search",
        "результати": "tradeatlas",
        "Email": "email"
    }
    source = source_map.get(tab_name, tab_name.lower())

    try:
        ws_client = sh.worksheet("Client")
        client_data = ws_client.get_all_records()
        client_df = pd.DataFrame(client_data)
    except:
        client_df = pd.DataFrame()

    existing_websites = set(client_df.get("Website", pd.Series(dtype=str)).str.lower().fillna(""))
    existing_emails = set(client_df.get("Email", pd.Series(dtype=str)).str.lower().fillna(""))

    try:
        ws_source = sh.worksheet(tab_name)
        source_data = ws_source.get_all_records()
    except:
        return []

    new_df = pd.DataFrame(source_data)
    new_clients = []

    for row in new_df.to_dict("records"):
        website = str(row.get("Website") or row.get("Сайт") or "").strip().lower()
        email = str(row.get("Email") or row.get("Пошта") or "").strip().lower()

        if website in existing_websites or email in existing_emails:
            continue

        new_clients.append({
            "Company": row.get("Company") or row.get("Назва") or row.get("Назва компанії") or "",
            "Website": website,
            "Email": email,
            "Contact person": row.get("Contact person") or "",
            "Phone": row.get("Phone") or "",
            "Brand": row.get("Brand") or "",
            "Product": row.get("Product") or row.get("Продукт") or "",
            "Quantity": row.get("Quantity") or row.get("Кількість") or "",
            "Country": row.get("Country") or row.get("Країна") or "",
            "Source": source,
            "Status": "New",
            "Deal value": "",
            "GPT": "",
            "Client": ""
        })

    return new_clients
