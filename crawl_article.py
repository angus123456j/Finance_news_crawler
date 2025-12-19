
# imports two functions from your db.py:
# insert_article(...): saves an article into your database
# article_exists(url): returns True if you already stored that URL (dedup)
from db import insert_article, article_exists



# requests: makes HTTP requests (downloads web pages / API responses).
# BeautifulSoup: parses HTML so you can find tags and extract text.
import requests
from bs4 import BeautifulSoup


# datetime: for parsing timestamps like "2025-12-17 18:22:30"
# date: represents just a date (YYYY-MM-DD)
from datetime import datetime
from datetime import date

# time: used for time.time() and sleeping (rate limiting).
# argparse: lets you run the script like python crawl_article.py --date 2025-12-16.
import time 
import argparse # need further understanding


# These are sent with HTTP requests.
# User-Agent: makes the site think it’s a real browser.
# Accept-Language: asks for Chinese content.
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
    "Accept-Language": "zh-CN,zh;q=0.9"
} 


#Function that crawls all Eastmoney articles for a given date.
def crawl_day(target_date: datetime.date):
    
    # start from page 1 of the list API
    # total_articles counts how many you saved
    page = 1
    total_articles = 0


    # Fetch one page of article list results from Eastmoney API.
    # articles becomes a list of dicts like:
    while True:
        
        articles = fetch_list_page(page)

        # If the API returns nothing, stop crawling.
        if not articles:
            print("[INFO] No articles returned, stopping.")
            break

        # boolean stop flag, articles will be connsidered until we reach an article that is older than the chosen date, 
        # then we know we don't have to look further or go to the next page because it will only be odler and older content.
        found_older = False

        # For each article item, take its datetime and reduce to just a date.
        # Example: 2025-12-17 18:22:30 → 2025-12-17
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
            # If your DB already has that URL, skip inserting again.
            if article_exists(item["url"]):
                continue

            # Calls fetch_article(url, media_name):
            # downloads the article HTML page
            # parses source, title, content, time
            source_cn, site_url, title, content, article_time = fetch_article(
                item["url"],
                item["mediaName"]
            )

            # Saves the article into your DB with whatever schema insert_article uses.
            insert_article(
                source=source_cn,
                url=item["url"],
                title=title,
                content=content,
                article_time=article_time
            )

            # Increment total and print success.
            total_articles += 1
            print(f"[OK] Saved: {title}")

        # Once you see older content, you’re “done” because pages will only get older.
        if found_older:
            print("[INFO] Reached older articles, stopping pagination.")
            break

        # enables crawler to move to the next page
        page += 1
        # cwaler has a rate limit so it doesn't get detected as a bot easily
        time.sleep(1)

    print(f"[DONE] Total articles saved: {total_articles}")


def fetch_list_page(page: int):

    # eastmoney article pages api
    api_url = "https://np-listapi.eastmoney.com/comm/web/getNewsByColumns"

    # column=355: the “category” you’re crawling
    # page_index: which page
    # page_size=20: 20 items per page
    # fields: asks the API what info to return per item
    # req_trace: random-ish value to mimic real requests
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

    # Makes the request
    # Raises error if status isn’t 200 OK
    resp = requests.get(api_url, params=params, headers=HEADERS, timeout=30)
    resp.raise_for_status()

    # Parse JSON response
    # Print how many items returned
    data = resp.json()
    print(f"[DEBUG] Page {page} returned {len(data.get('data', {}).get('list', []))} items")

    # prepares results list
    articles = []

    # Loop through each returned article in the API response.
    for item in data.get("data", {}).get("list", []):

        # retrieves the article url, the raw/publish time and media_name which is source_media name
        url = item.get("uniqueUrl")
        raw_time = item.get("showTime")
        media_name = item.get("mediaName")

        # if the article is missing key fields such as url or publish time skip it
        if not url or not raw_time:
            continue
        
        # Convert time string into a Python datetime.
        try:
            publish_time = datetime.strptime(raw_time, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            continue
        
        # cleanly add the newly scarpaed article with its url, publish time and mediam name
        articles.append({
            "url": url,
            "publish_time": publish_time,
            "mediaName": media_name
        })

    # return the list of articles for that page
    return articles


 
# Utility function to normalize text.
def clean_text(text: str) -> str:
    """
    Simple cleaner: strips leading/trailing spaces and
    collapses multiple blank lines into single ones.
    """
    lines = [line.strip() for line in text.splitlines()]
    non_empty = [line for line in lines if line]
    return '\n'.join(non_empty)



def fetch_article(url, media_name=None):

    # Downloads the article HTML page.
    response = requests.get(url, headers=HEADERS, timeout=30)
    response.raise_for_status()

    # Parses HTML using the fast lxml parser.
    soup = BeautifulSoup(response.text, "lxml")

    # Looks for <div class="infos"> (Eastmoney’s metadata block)
    source_cn = None
    infos = soup.find("div", class_="infos")

    # Iterate metadata items
    # Find the one that starts with “来源：”
    # Extract the source text
    if infos:
        for div in infos.find_all("div", class_="item"):
            text = div.get_text(strip=True)
            if text.startswith("来源："):
                source_cn = text.replace("来源：", "").strip()
                break

    # HARD GUARANTEE (never NULL)
    # if source not found, use API’s mediaName
    # if even that missing, default "东方财富"
    if not source_cn:
        source_cn = media_name or "东方财富"

    # Sometimes the page has a logo link, this extracts its href link
    site_logo = soup.find("a", class_="emlogo")
    site_url = site_logo["href"] if site_logo else None

    # extract title 
    title_tag = soup.find("div", class_="title")
    title = title_tag.get_text(strip=True) if title_tag else ""

    # extract the actual article content
    article_div = soup.find("div", id="ContentBody")
    content = article_div.get_text("\n", strip=True) if article_div else ""

    # extract the artilce time
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


# old debugging utility function
def save_article_to_file(title: str, content: str, filename: str = "outputs/article_zh.txt"):
    with open(filename, "w", encoding="utf-8") as f:
        f.write("【标题】\n")
        f.write(title + "\n\n")
        f.write("【正文】\n")
        f.write(content)





# Runs only when you execute this script directly.
if __name__ == "__main__":
    # Reads --date.
    parser = argparse.ArgumentParser(description="Eastmoney daily article crawler")

    parser.add_argument(
        "--date",
        type=str,
        help="Target date in YYYY-MM-DD format (default: today)"
    )

    args = parser.parse_args()

    # If date is given, parse it; otherwise default to today.
    if args.date:
        try:
            target_date = datetime.strptime(args.date, "%Y-%m-%d").date()
        except ValueError:
            raise ValueError("Date must be in YYYY-MM-DD format")
    else:
        target_date = datetime.now().date()

    # Start crawl.
    print(f"[INFO] Crawling articles for date: {target_date}")
    crawl_day(target_date)
