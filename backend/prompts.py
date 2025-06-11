def prompt_is_potential_client(title, description, url, website=None):
    return f"""
    Company Name (title): {title}
    Description: {description}
    Search Result URL: {url}
    Website: {website or "Not provided"}

    Task:
    Determine whether this company is a potential client for a business that sells medical or NDT X-ray films.
    Every other medical dealer, distributor - even if in another medical field - is our potential partner.
    Important:
    - If this is a OEM manufacturer or official brand like Fujifilm, Agfa, Carestream, etc — answer No.
    - If it’s a distributor, clinic, dealer, importer, medical center — answer Yes.

    Respond ONLY:
    Client: Yes or Client: No
    """


def prompt_is_company_website(title: str, description: str, url: str) -> str:
    return f"""
    Company Name: {title}
    Page Description: {description}
    URL: {url}

    Task:
    Determine whether this is the official website of the company. Ignore marketplaces, directories, Wikipedia, aggregators, partners, or forums.

    Consider only:
    - The company name being explicitly mentioned on the page
    - Company logo or direct contact details
    - Domain matching the company name (e.g., carestream → carestream.com)

    If none of these are found, assume it's not the official website.

    Respond only in this format:
    Company Website: Yes or Company Website: No
    """


def prompt_get_category(title: str, description: str, url: str) -> str:
    return f"""
    Company Name: {title}
    Description: {description}
    URL: {url}

    What type of company is this? Choose one of the following categories:
    Medical / NDT / Other

    Response format:
    Category: ...
    """


def prompt_get_country(description: str, url: str) -> str:
    return f"""
    Description or snippet about the company: {description}
    URL: {url}

    In which country is this company most likely located?

    Response format:
    Country: ... (Only name)
    If can not find out - asnwer just black space, nothing.
    """
def prompt_get_company_name(page_text: str, url: str) -> str:
    return f"""
You are given raw website text from a company's homepage. Extract the official name of the company.

Website: {url}

Page text (cut): {page_text}

Rules:
- Do not include slogans, marketing phrases, product names.
- Focus on extracting the registered company name.
- Ignore generic phrases like “Buy X-ray film” or “Welcome to our website”.

Respond in this format only:
Company Name: ...
"""
