from db import insert_article, article_exists
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from datetime import date

import time
import argparse



HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
    "Accept-Language": "zh-CN,zh;q=0.9"
}
def crawl_day(target_date: datetime.date):
    page = 1
    total_articles = 0

    while True:
        articles = fetch_list_page(page)

        if not articles:
            print("[INFO] No articles returned, stopping.")
            break

        found_older = False

        for item in articles:
            publish_date = item["publish_time"].date()

            # Newer than target → skip
            if publish_date > target_date:
                continue

            # Older than target → stop after this page
            if publish_date < target_date:
                found_older = True
                continue

            # Dedup
            if article_exists(item["url"]):
                continue

            source_cn, site_url, title, content, article_time = fetch_article(
                item["url"],
                item["mediaName"]
            )

            insert_article(
                source=source_cn,
                url=item["url"],
                title=title,
                content=content,
                article_time=article_time
            )

            total_articles += 1
            print(f"[OK] Saved: {title}")

        if found_older:
            print("[INFO] Reached older articles, stopping pagination.")
            break

        page += 1
        time.sleep(1)

    print(f"[DONE] Total articles saved: {total_articles}")


def fetch_list_page(page: int):
    api_url = "https://np-listapi.eastmoney.com/comm/web/getNewsByColumns"

    params = {
        "client": "web",
        "biz": "web_news_col",
        "column": "355",
        "order": 1,
        "needInteractData": 0,
        "page_index": page,
        "page_size": 20,
        "fields": "code,showTime,title,mediaName,summary,image,url,uniqueUrl,Np_dst",
        "types": "1,20",
        "req_trace": str(int(time.time() * 1000)),
    }

    resp = requests.get(api_url, params=params, headers=HEADERS, timeout=30)
    resp.raise_for_status()

    data = resp.json()
    print(f"[DEBUG] Page {page} returned {len(data.get('data', {}).get('list', []))} items")

    articles = []

    for item in data.get("data", {}).get("list", []):
        url = item.get("uniqueUrl")
        raw_time = item.get("showTime")
        media_name = item.get("mediaName")

        if not url or not raw_time:
            continue

        try:
            publish_time = datetime.strptime(raw_time, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            continue

        articles.append({
            "url": url,
            "publish_time": publish_time,
            "mediaName": media_name
        })

    return articles

 

def clean_text(text: str) -> str:
    """
    Simple cleaner: strips leading/trailing spaces and
    collapses multiple blank lines into single ones.
    """
    lines = [line.strip() for line in text.splitlines()]
    non_empty = [line for line in lines if line]
    return '\n'.join(non_empty)



def fetch_article(url, media_name=None):
    response = requests.get(url, headers=HEADERS, timeout=30)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "lxml")

    source_cn = None
    infos = soup.find("div", class_="infos")

    if infos:
        for div in infos.find_all("div", class_="item"):
            text = div.get_text(strip=True)
            if text.startswith("来源："):
                source_cn = text.replace("来源：", "").strip()
                break

    # HARD GUARANTEE (never NULL)
    if not source_cn:
        source_cn = media_name or "东方财富"

    site_logo = soup.find("a", class_="emlogo")
    site_url = site_logo["href"] if site_logo else None

    title_tag = soup.find("div", class_="title")
    title = title_tag.get_text(strip=True) if title_tag else ""

    article_div = soup.find("div", id="ContentBody")
    content = article_div.get_text("\n", strip=True) if article_div else ""

    article_time = None
    if infos:
        time_div = infos.find("div", class_="item")
        if time_div:
            raw_time = time_div.get_text(strip=True)
            try:
                article_time = datetime.strptime(raw_time, "%Y年%m月%d日 %H:%M")
            except ValueError:
                pass

    return source_cn, site_url, title, content, article_time



def save_article_to_file(title: str, content: str, filename: str = "outputs/article_zh.txt"):
    with open(filename, "w", encoding="utf-8") as f:
        f.write("【标题】\n")
        f.write(title + "\n\n")
        f.write("【正文】\n")
        f.write(content)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Eastmoney daily article crawler")

    parser.add_argument(
        "--date",
        type=str,
        help="Target date in YYYY-MM-DD format (default: today)"
    )

    args = parser.parse_args()

    if args.date:
        try:
            target_date = datetime.strptime(args.date, "%Y-%m-%d").date()
        except ValueError:
            raise ValueError("Date must be in YYYY-MM-DD format")
    else:
        target_date = datetime.now().date()

    print(f"[INFO] Crawling articles for date: {target_date}")
    crawl_day(target_date)
