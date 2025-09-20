import os
import requests
from datetime import datetime
from dotenv import load_dotenv
from newsdataapi import NewsDataApiClient

load_dotenv()

# NewsData API 사용
api_key_newsdata = os.getenv("LATEST_NEWS_API_KEY_NEWSDATA")
api = NewsDataApiClient(apikey=api_key_newsdata)

def fetch_newsdata_latest():
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

    return news_list

fetch_newsdata_latest()

# Coindesk API 사용 (무료 플랜은 11,000 크레딧/월, 최대 250,000 Total)
api_key_coindesk = os.getenv("COINDESK_API_KEY")
BASE_URL = "https://data-api.coindesk.com/news/v1"


# 최신 뉴스 (Latest Articles 3 크래딧 소모)
def fetch_latest():
    url = f"{BASE_URL}/article/list"
    params = {"lang": "EN", "limit": 3, "apikey": api_key_coindesk}
    response = requests.get(url, params=params)
    data = response.json().get("Data", [])

    articles = []
    for a in data:
        ts = a.get("PUBLISHED_ON")
        date_str = (
            datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S") if ts else "N/A"
        )

        articles.append(
            {
                "title": a.get("TITLE"),
                "sentiment": a.get("SENTIMENT"),
                "date": date_str,
            }
        )
    return articles

# 뉴스 검색 (News Search 3 크래딧 소모)
def fetch_search(keyword, source_key="coindesk"):
    url = f"{BASE_URL}/search"
    params = {
        "search_string": keyword,
        "lang": "EN",
        "limit": 3,
        "source_key": source_key,
        "apikey": api_key_coindesk,
    }
    response = requests.get(url, params=params)
    data = response.json().get("Data", [])

    results = []
    for a in data:
        ts = a.get("PUBLISHED_ON")
        date_str = (
            datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S") if ts else "N/A"
        )
        results.append(
            {
                "title": a.get("TITLE"),
                "sentiment": a.get("SENTIMENT"),
                "date": date_str,
            }
        )

    return results


def get_all_news(search_keyword):
    
    news_list = fetch_newsdata_latest()
    for n in news_list:
        print(f"{n['date']}")
        print(f"{n['title']}")
        print(n["summary"])
        print("-" * 50)

    results = fetch_latest()
    for r in results:
        print(r["date"], r["title"], r["sentiment"])
        print("-" * 50)
    
    search_results = fetch_search(search_keyword)

    for r in search_results:
        print(r["date"], r["title"], r["sentiment"])
        print("-" * 50)

get_all_news("Ethereum")
