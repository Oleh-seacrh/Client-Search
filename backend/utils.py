from backend.prompts import (
    prompt_is_potential_client,
    prompt_is_company_website,
    prompt_get_category,
    prompt_get_country,
    prompt_get_company_name  # новий
)
from backend.utils import call_gpt, extract_email, simplify_url

def analyze_site(result: dict) -> dict or None:
    """
    GPT-аналітика одного результату пошуку. Повертає dict, або None якщо не підходить.
    """
    title = result.get("title", "")
    description = result.get("description", "")
    link = result.get("link", "")
    simplified_url = simplify_url(link)

    try:
        gpt_verdict = call_gpt(prompt_is_potential_client(title, description, link, simplified_url))
        gpt_company_name = call_gpt(prompt_get_company_name(description, link))
        gpt_category = call_gpt(prompt_get_category(title, description, link))
        gpt_country = call_gpt(prompt_get_country(description, link))
    except Exception:
        return None

    # Виробники — відсікаємо
    if "manufacturer" in gpt_verdict.lower() or "producer" in gpt_verdict.lower():
        return None

    # Не клієнт — відсікаємо
    if "client: no" in gpt_verdict.lower():
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
