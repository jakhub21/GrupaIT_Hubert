import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
import time


def fetch_google_results(query, num_results=10):
    '''Function to fetch Google search results for a given query'''
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36"
    }
    search_url = f"https://www.google.com/search?q={query.replace(' ', '+')}&num={num_results}"
    response = requests.get(search_url, headers=headers, timeout=10)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    results = []

    for result in soup.select("span.VuuXrf"):
        name = result.get_text(strip=True)
        results.append(name)

    links = []
    for link in soup.select("a[href]"):
        href = link["href"]
        if "/url?q=" in href:
            links.append(href.split("/url?q=")[1].split("&")[0])

    return results, links


def fetch_nip_for_company(company_name):
    '''Function to fetch NIP for a given company name'''
    try:
        search_query = f"{company_name} NIP"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36"
        }
        search_url = f"https://www.google.com/search?q={search_query.replace(' ', '+')}"
        response = requests.get(search_url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        text_elements = soup.stripped_strings
        for text in text_elements:
            match = re.search(r"NIP[:\s]*([\d\s\-]{10,})", text)
            if match:
                return match.group(1).replace(" ", "").replace("-", "")

        bold_elements = soup.find_all("b")
        for bold in bold_elements:
            match = re.search(r"([\d\s\-]{10,})", bold.get_text())
            if match:
                return match.group(1).replace(" ", "").replace("-", "")

    except requests.RequestException as e:
        print(f"Error fetching NIP for company {company_name}: {e}")
    return "No data"


def fetch_krs_for_company(company_name):
    '''Function to fetch KRS number for a given company name'''
    try:
        search_query = f"{company_name} KRS"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36"
        }
        search_url = f"https://www.google.com/search?q={search_query.replace(' ', '+')}"
        response = requests.get(search_url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        text_elements = soup.stripped_strings
        for text in text_elements:
            if "KRS" in text:
                match = re.search(r"KRS[:\s]*(\d{10})", text)
                if match:
                    return match.group(1)
    except requests.RequestException as e:
        print(f"Error fetching KRS for company {company_name}: {e}")
    return None


def fetch_ceo_and_nip_from_krs(krs_number):
    '''Function to fetch CEO and NIP from KRS API for a given KRS number'''
    try:
        url = f"https://api-krs.ms.gov.pl/api/krs/OdpisAktualny/{krs_number}?rejestr=P&format=json"
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()

        section_2 = data.get("odpis", {}).get("dane", {}).get("dzial2", {})
        representation = section_2.get("reprezentacja", {})
        members = representation.get("sklad", [])

        ceo = "No data"
        for member in members:
            if "PREZES ZARZĄDU" in member.get("funkcjaWOrganie", "").upper():
                last_name = member.get("nazwisko", {}).get("nazwiskoICzlon", "No data")
                first_name = member.get("imiona", {}).get("imie", "No data")
                ceo = f"{first_name} {last_name}"
                break

        section_1 = data.get("odpis", {}).get("dane", {}).get("dzial1", {})
        nip = section_1.get("danePodmiotu", {}).get("identyfikatory", {}).get("nip", "No data")

        return ceo, nip
    except requests.RequestException as e:
        print(f"Error fetching data from KRS API for KRS {krs_number}: {e}")
    return "No data", "No data"


def main():
    '''Main function to process companies and generate CSV'''
    search_query = "producent karmy dla psów i kotów"
    num_results = 20
    companies = []

    print("Searching for companies in Google...")
    try:
        company_names, _ = fetch_google_results(search_query, num_results)

        unique_company_names = list(dict.fromkeys(company_names))
        print(f"Found unique company names: {unique_company_names}")

        for company_name in unique_company_names:
            if len(companies) >= 10:
                break

            print(f"Processing company: {company_name}")

            krs = fetch_krs_for_company(company_name)
            ceo, nip = fetch_ceo_and_nip_from_krs(krs) if krs else ("No data", "No data")

            companies.append({
                "Company": company_name,
                "NIP": nip,
                "CEO": ceo
            })
            time.sleep(1)

        df = pd.DataFrame(companies)
        df.to_csv("companies.csv", index=False, encoding="utf-8")
        print("Data saved to companies.csv")
        print(df)

    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
