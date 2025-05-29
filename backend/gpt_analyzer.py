import re
import streamlit as st
from backend.utils import call_gpt
from backend.gsheet_service import get_gsheet_client
from backend.prompts import prompt_is_company_website


def analyze_sites_from_results(spreadsheet_id: str, limit: int = 20) -> list[str]:
    gc = get_gsheet_client()
    sh = gc.open_by_key(spreadsheet_id)

    try:
        sheet = sh.worksheet("результати")
    except:
        return ["❌ Вкладка 'результати' не знайдена."]

    data = sheet.get_all_values()
    headers = data[0]
    rows = data[1:]

    # Додаємо колонки, якщо відсутні
    required_cols = ["Категорія", "Висновок GPT"]
    for col in required_cols:
        if col not in headers:
            headers.append(col)
            sheet.update("A1", [headers])  # оновлення заголовка

    col_count = len(headers)
    analyze_indices = []
    for i, row in enumerate(rows):
        # Якщо Категорія або Висновок порожні
        if len(row) < col_count or row[col_count - 2].strip() == "" or row[col_count - 1].strip() == "":
            analyze_indices.append(i + 2)  # +2 бо 1-based, з другої строки
        if len(analyze_indices) >= limit:
            break

    logs = []
    for row_num in analyze_indices:
        row = sheet.row_values(row_num)
        title = row[0]
        url = row[1]

        # Запити до GPT
        try:
            category_prompt = prompt_get_category(title, "", url)
            verdict_prompt = prompt_is_potential_client(title, "", url, url)

            category_response = gpt_call(category_prompt)
            verdict_response = gpt_call(verdict_prompt)
        except Exception as e:
            logs.append(f"❌ Помилка GPT при обробці {title}: {e}")
            continue

        # Витягуємо відповіді
        category = "-"
        verdict = "-"

        cat_match = re.search(r"Категорія:\s*(.*)", category_response)
        if cat_match:
            category = cat_match.group(1).strip()

        verdict_match = re.search(r"Клієнт:\s*(.*)", verdict_response)
        if verdict_match:
            verdict = f"Клієнт: {verdict_match.group(1).strip()}"

        # Записуємо результат
        sheet.update_cell(row_num, col_count - 1, category)
        sheet.update_cell(row_num, col_count, verdict)
        logs.append(f"🔎 `{title}` → `{category}` / `{verdict}`")

    return logs
