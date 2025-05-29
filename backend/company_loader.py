from backend.gsheet_service import get_gsheet_client
import re
import streamlit as st

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
