def prompt_is_potential_client(title, description, url, website=None):
    return f"""
    Company Name (title): {title}
    Description: {description}
    Search Result URL: {url}
    Website: {website or "Not provided"}

    Task:
    Determine whether this company is a potential client for a business that sells medical or NDT X-ray films.
    We are a medical equipment company Medem. Our website is www.xraymedem.com
    Every other medical dealer, distributor - even if in another medical field - is our potential partner.
    Important:
    - If this is a manufacturer, producer, or official brand like Fujifilm, Agfa, Carestream, etc — answer No.
    - If it’s a distributor, clinic, dealer, importer, medical center — answer Yes.
    - If it's some legal, IT , logistics company - not our client

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
def prompt_get_company_name(description: str, url: str) -> str:
    return f"""
    Based on the following information:
    Description: {description}
    Website: {url}

    What is the official name of the company mentioned?
    Respond in this format:
    Company Name: ...
    """

