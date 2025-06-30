import os
import json
import requests
import openai
import gspread
from google.oauth2.service_account import Credentials

# Constants
SPREADSHEET_URL = "https://docs.google.com/spreadsheets/d/1ZNtOMTWPbfFBbssYAtuZSyCy5RWyvx69kFcMCsWByH8/edit"

TICKERS = ["NVDA", "SMCI", "PLTR", "LMT", "MRK", "BTC", "ETH", "EUR/USD"]
TICKER_SECTOR = {
    "NVDA": "Technology",
    "SMCI": "Technology",
    "PLTR": "Technology",
    "LMT": "Defense",
    "MRK": "Healthcare",
    "BTC": "Crypto",
    "ETH": "Crypto",
    "EUR/USD": "Forex"
}

NEWS_API_KEY = os.getenv("NEWS_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
SERVICE_ACCOUNT_FILE = os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE", "service_account.json")

openai.api_key = OPENAI_API_KEY


def fetch_news(ticker: str) -> str:
    """Fetch latest news articles for the ticker."""
    if not NEWS_API_KEY:
        return ""
    url = (
        "https://newsapi.org/v2/everything?" +
        f"q={ticker}&language=en&sortBy=publishedAt&pageSize=5&apiKey={NEWS_API_KEY}"
    )
    resp = requests.get(url, timeout=30)
    if resp.status_code != 200:
        return ""
    articles = resp.json().get("articles", [])
    return "\n".join(
        f"{a.get('title', '')}. {a.get('description', '')}" for a in articles
    )


def analyze_text(ticker: str, news_text: str) -> dict:
    """Use OpenAI API to analyze sentiment and other metrics."""
    prompt = f"""
Jsi zkušený finanční analytik. Na základě následujících zpráv a informací o instrumentu {ticker}
proveď analýzu v češtině.

Vrať JSON se strukturou:
{{"sentiment":"pozitivní|negativní|neutrální",
  "summary":"stručné shrnutí v češtině",
  "recommendation":"Zvaž nákup|Zvaž short|Dlouhodobě sledovat|Vynechat",
  "risk":0-100,
  "keywords":"klíčová slova"}}

Zprávy:
{news_text}
"""
    response = openai.ChatCompletion.create(
        model="gpt-4-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
    )
    content = response.choices[0].message["content"]
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        return {
            "sentiment": "neutrální",
            "summary": "",
            "recommendation": "Dlouhodobě sledovat",
            "risk": 50,
            "keywords": ""
        }


def append_to_sheet(row: list):
    """Append a row to the Google Sheet."""
    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    creds = Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=scopes
    )
    client = gspread.authorize(creds)
    sheet = client.open_by_url(SPREADSHEET_URL).sheet1
    sheet.append_row(row)


def main():
    for ticker in TICKERS:
        news_text = fetch_news(ticker)
        analysis = analyze_text(ticker, news_text)
        sector = TICKER_SECTOR.get(ticker, "Unknown")
        row = [
            ticker,
            sector,
            analysis.get("sentiment", ""),
            analysis.get("summary", ""),
            analysis.get("recommendation", ""),
            analysis.get("risk", ""),
            analysis.get("keywords", "")
        ]
        append_to_sheet(row)
        print(f"Processed {ticker}")


if __name__ == "__main__":
    main()
def append_to_sheet(worksheet, data):
    """
    Zapíše jeden řádek do Google Sheetu.
    """
    worksheet.append_row(data, value_input_option="USER_ENTERED")
