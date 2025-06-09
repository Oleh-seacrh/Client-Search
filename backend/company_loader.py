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

    # Готуємо або створюємо вкладку "компанії"
    try:
        company_sheet = sh.worksheet("компанії")
        existing = set(name.strip().upper() for name in company_sheet.col_values(1)[1:])
    except:
        company_sheet = sh.add_worksheet(title="компанії", rows="1000", cols="1")
        company_sheet.update("A1", [["Компанії"]])
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

        # Прибираємо лапки та зайві пробіли
        name = name.replace("«", "").replace("»", "").replace("\"", "")
        name = ' '.join(name.split())

        if len(name) > 2:
            cleaned = name.upper()
            if cleaned in existing or cleaned in [x[0] for x in new_entries]:
                log_output.append(f"🔁 Пропущено повтор: {original}")
            else:
                new_entries.append([cleaned])
                log_output.append(f"➕ Додано: {cleaned}")

    # Додаємо у таблицю
    if new_entries:
        next_row = len(existing) + 2  # 1-based, з урахуванням заголовка
        company_sheet.update(f"A{next_row}:A{next_row + len(new_entries) - 1}", new_entries)

    return log_output, len(new_entries)
    
def get_new_clients_from_tab(tab_name: str):
    gc = get_gsheet_client()
    sh = gc.open_by_key(st.secrets["spreadsheet_id"])
    
    source_map = {
        "Аналіз": "Search",
        "результати": "TradeAtlas",
        "Email": "Email"
    }
    source = source_map.get(tab_name, "Unknown")

    # Читаємо вкладку Client
    try:
        ws_client = sh.worksheet("Client")
        client_data = ws_client.get_all_records()
        client_df = pd.DataFrame(client_data)
    except:
        client_df = pd.DataFrame()

    # Безпечна перевірка колонок
    existing_websites = set(client_df.get("Сайт", pd.Series(dtype=str)).str.lower().fillna(""))
    existing_emails = set(client_df.get("Email", pd.Series(dtype=str)).str.lower().fillna(""))

    # Читаємо джерельну вкладку
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

        # Безпечне формування полів: якщо немає — вставляється ""
        new_clients.append({
            "Company": row.get("Company") or row.get("Назва") or row.get("Назва компанії") or "",
            "Website": website,
            "Email": email,
            "Contact person": row.get("Contact person", ""),
            "Brand": row.get("Brand", ""),
            "Product": row.get("Product") or row.get("Продукт") or "",
            "Quantity": row.get("Quantity") or row.get("Кількість") or "",
            "Country": row.get("Country") or row.get("Країна") or "",
            "Source": source,
            "Status": "Новий",
            "Deal value": ""
        })

    return new_clients
