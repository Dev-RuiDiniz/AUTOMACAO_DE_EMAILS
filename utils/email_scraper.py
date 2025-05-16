import requests
from bs4 import BeautifulSoup
import re
import pandas as pd
from urllib.parse import urlparse
from datetime import datetime
import os

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
}

EMAILS_INVALIDOS = [
    "contato", "suporte", "admin", "no-reply", "noreply", "email", "atendimento", "vendas"
]
DOMINIOS_DESCARTADOS = [
    "yahoo.com", "hotmail.com", "live.com"
]

# Lista de palavras-chave para buscar recrutadores em áreas diferentes
QUERIES = [
    "recrutador tecnologia São Paulo site:.br",
    "recrutador RH site:.br",
    "empresa desenvolvedora vagas contato site:.br",
    "empresa de TI contato recrutamento site:.br",
    "vaga Python recrutamento empresa site:.br",
]

def search_urls(query, num_pages=3):
    urls = []
    for page in range(num_pages):
        start = page * 10
        response = requests.get(
            f"https://www.bing.com/search?q={query}&first={start}",
            headers=HEADERS
        )
        soup = BeautifulSoup(response.text, "html.parser")
        for h2 in soup.find_all("h2"):
            a_tag = h2.find("a")
            if a_tag and a_tag["href"].startswith("http"):
                urls.append(a_tag["href"])
    return urls

def is_email_valido(email):
    usuario, dominio = email.split("@")
    if dominio.lower() in DOMINIOS_DESCARTADOS:
        return False
    if any(invalido in usuario.lower() for invalido in EMAILS_INVALIDOS):
        return False
    return True

def extract_emails_from_url(url):
    try:
        response = requests.get(url, headers=HEADERS, timeout=5)
        raw_emails = re.findall(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", response.text)
        valid_emails = [e for e in set(raw_emails) if is_email_valido(e)]
        domain = urlparse(url).netloc
        return valid_emails, domain
    except:
        return [], None

def scrape_multiple_queries(queries, max_sites=10, pages_per_query=3):
    seen_emails = set()
    results = []

    for query in queries:
        print(f"\n🔍 Buscando: '{query}'")
        urls = search_urls(query, num_pages=pages_per_query)

        for url in urls[:max_sites]:
            emails, domain = extract_emails_from_url(url)
            for email in emails:
                if email not in seen_emails:
                    seen_emails.add(email)
                    results.append({
                        "empresa": domain,
                        "email": email,
                        "fonte": url,
                        "busca": query
                    })

    if results:
        df = pd.DataFrame(results)
        os.makedirs("output", exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_path = f"output/emails_{timestamp}.csv"
        df.to_csv(file_path, index=False)
        print(f"\n✅ {len(df)} e-mails salvos em '{file_path}'.")
    else:
        print("\n⚠️ Nenhum e-mail válido encontrado.")

if __name__ == "__main__":
    scrape_multiple_queries(QUERIES, max_sites=15, pages_per_query=3)
