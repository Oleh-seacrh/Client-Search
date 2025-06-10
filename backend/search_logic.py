from backend.prompts import (
    prompt_is_potential_client,
    prompt_is_company_website,
    prompt_get_category,
    prompt_get_country
)
from backend.utils import call_gpt, extract_email, simplify_url, get_page_text
from backend.gsheet_service import get_worksheet_by_name, read_existing_websites, append_rows
import streamlit as st
import requests


def google_search(keyword: str, limit: int = 20, offset: int = 0) -> list:
    """
    Виконує реальний Google Search через Programmable Search API.
    """
    api_key = st.secrets["GOOGLE_API_KEY"]
    cse_id = st.secrets["CSE_ID"]

    results = []
    start = offset + 1  # Google API index starts at 1

    while len(results) < limit:
        num = min(10, limit - len(results))
        params = {
            "key": api_key,
            "cx": cse_id,
            "q": keyword,
            "start": start,
            "num": num,
        }

        response = requests.get("https://www.googleapis.com/customsearch/v1", params=params)
        if response.status_code != 200:
            raise Exception(f"Google Search error: {response.status_code} {response.text}")

        data = response.json()
        items = data.get("items", [])
        for item in items:
            results.append({
                "title": item.get("title", ""),
                "description": item.get("snippet", ""),
                "link": item.get("link", "")
            })

        if "nextPage" in data.get("queries", {}):
            start = data["queries"]["nextPage"][0]["startIndex"]
        else:
            break

    return results[:limit]


def analyze_site(result: dict) -> dict | None:
    """
    GPT-аналітика одного результату пошуку.
    """
    title = result.get("title", "")
    description = result.get("description", "")
    link = result.get("link", "")
    simplified_url = simplify_url(link)

    # Завантажуємо текст із сайту
    page_text = get_page_text(simplified_url)

    try:
        gpt_verdict = call_gpt(prompt_is_potential_client(title, description, link, simplified_url))
        gpt_company_name = call_gpt(prompt_get_company_name(page_text, simplified_url))
        gpt_category = call_gpt(prompt_get_category(title, description, link))
        gpt_country = call_gpt(prompt_get_country(description, link))
    except Exception:
        return None

    if "client: no" in gpt_verdict.lower():
        return None
    if "manufacturer" in gpt_verdict.lower() or "producer" in gpt_verdict.lower():
        return None

    return {
        "Company": gpt_company_name.replace("Company Name:", "").strip() or title,
        "Website": simplified_url,
        "Email": extract_email(description),
        "Category": gpt_category.replace("Category:", "").strip(),
        "Country": gpt_country.replace("Country:", "").strip(),
        "Client": "Yes",
        "GPT": gpt_verdict.strip(),
        "Description": description,
        "Source": "search"
    }


def perform_search_and_analysis(
    keyword: str,
    gsheet_client,
    spreadsheet_id: str,
    only_new: bool = True,
    limit: int = 20,
    offset: int = 0
):
    """
    Виконує реальний Google Search та GPT аналіз результатів.
    Додає тільки підтверджених GPT клієнтів у вкладку 'Client'.
    """
    search_results = google_search(keyword, limit=limit, offset=offset)

    sheet = gsheet_client.open_by_key(spreadsheet_id)
    ws = get_worksheet_by_name(sheet, "Client")

    existing_websites = read_existing_websites(ws) if only_new else []
    new_results = []

    for result in search_results:
        if result is None or not isinstance(result, dict):
            continue

        url = simplify_url(result.get("link", ""))
        if only_new and url in existing_websites:
            continue

        enriched = analyze_site(result)
        if enriched:  # enriched is None if GPT said 'not a client'
            new_results.append(enriched)

    if new_results:
        append_rows(ws, new_results)

    return new_results
