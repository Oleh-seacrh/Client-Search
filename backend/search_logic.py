from backend.prompts import (
    prompt_is_potential_client,
    prompt_is_company_website,
    prompt_get_category,
    prompt_get_country
)
from backend.utils import call_gpt, extract_email, simplify_url
from backend.gsheet_service import get_worksheet_by_name, read_existing_urls, append_rows


def analyze_site(result: dict) -> dict:
    """
    Аналізує один результат (title, description, link) через GPT.
    """
    title = result.get("title", "")
    description = result.get("description", "")
    link = result.get("link", "")
    simplified_url = simplify_url(link)

    try:
        gpt_client = call_gpt(prompt_is_potential_client(title, description, link))
        gpt_company = call_gpt(prompt_is_company_website(title, description, link))
        gpt_category = call_gpt(prompt_get_category(title, description, link))
        gpt_country = call_gpt(prompt_get_country(description, link))
    except Exception:
        gpt_client = gpt_company = gpt_category = gpt_country = "GPT Error"

    email = extract_email(description)

    return {
        "Назва": title,
        "Сайт": simplified_url,
        "Email": email,
        "Категорія": gpt_category.replace("Категорія:", "").strip(),
        "Країна": gpt_country.replace("Країна:", "").strip(),
        "GPT: Клієнт": gpt_client.replace("Клієнт:", "").strip(),
        "GPT: Сайт компанії": gpt_company.replace("Сайт компанії:", "").strip(),
        "Опис": description,
        "Джерело": link
    }


def perform_search_and_analysis(keyword: str, gsheet_client, spreadsheet_id: str, only_new: bool = True, limit: int = 20, offset: int = 0):
    """
    Симуляційна функція пошуку та GPT-аналізу результатів (поки без реального Google Search).
    """
    # 🔁 Тут має бути реальний Google Search (поки фейкові дані)
    search_results = [
        {
            "title": f"{keyword} Company {i}",
            "description": f"Distributor of imaging products. Email: contact{i}@example.com",
            "link": f"https://example{i}.com"
        }
        for i in range(offset, offset + limit)
    ]

    sheet = gsheet_client.open_by_key(spreadsheet_id)
    ws = get_worksheet_by_name(sheet, "результати")

    existing_urls = read_existing_urls(ws) if only_new else []
    new_results = []

    for result in search_results:
        url = simplify_url(result.get("link", ""))
        if only_new and url in existing_urls:
            continue
        enriched = analyze_site(result)
        new_results.append(enriched)

    append_rows(ws, new_results)
    return new_results
