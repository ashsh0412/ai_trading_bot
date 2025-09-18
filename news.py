import os
import requests
from datetime import datetime
from dotenv import load_dotenv
from newsdataapi import NewsDataApiClient

load_dotenv()

# NewsData API 사용
api_key_newsdata = os.getenv("LATEST_NEWS_API_KEY_NEWSDATA")
api = NewsDataApiClient(apikey=api_key_newsdata)

response = api.latest_api(
    q="cryptocurrency",
    max_result=10,  # 기사 수 제한 10개 (1 크레딧 당 10개 기사)
    scroll=False,
)

news_list = [
    {
        "date": a["pubDate"],
        "title": a["title"],
        "summary": a.get("description", ""),
    }
    for a in response.get("results", [])
]

for n in news_list:
    print(f"{n['date']}")
    print(f"{n['title']}")
    print(n["summary"])
    print("-" * 50)

# Coindesk API 사용 (무료 플랜은 11,000 크레딧/월, 최대 250,000 Total)
api_key_coindesk = os.getenv("COINDESK_API_KEY")
BASE_URL = "https://data-api.coindesk.com/news/v1"


# 최신 뉴스 (Latest Articles 3 크래딧 소모)
def fetch_latest(limit=3):
    url = f"{BASE_URL}/article/list"
    params = {"lang": "EN", "limit": limit, "apikey": api_key_coindesk}
    response = requests.get(url, params=params)
    data = response.json().get("Data", [])

    print("\n=== Latest Articles ===")
    for a in data:
        ts = a.get("PUBLISHED_ON")
        date_str = datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S") if ts else "N/A"

        print(f"Title: {a.get('TITLE')}")
        print(f"Sentiment: {a.get('SENTIMENT')}")
        print(f"Date: {date_str}")
        print("-" * 50)


# 뉴스 검색 (News Search 3 크래딧 소모)
def fetch_search(keyword, limit=3, source_key="coindesk"):
    url = f"{BASE_URL}/search"
    params = {
        "search_string": keyword,
        "lang": "EN",
        "limit": limit,
        "source_key": source_key,
        "apikey": api_key_coindesk,
    }
    response = requests.get(url, params=params)
    data = response.json().get("Data", [])

    print(f"\n=== Search Results: {keyword} ===")

    for a in data:
        ts = a.get("PUBLISHED_ON")
        date_str = datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S") if ts else "N/A"

        print(f"Title: {a.get('TITLE')}")
        print(f"Sentiment: {a.get('SENTIMENT')}")
        print(f"Date: {date_str}")
        print("-" * 50)


if __name__ == "__main__":
    fetch_latest()
    fetch_search("Ethereum")