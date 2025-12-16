import os
import logging
from openai import OpenAI
from db import get_article_by_id, insert_rewritten_article
from prompt_builder import build_rewrite_prompt
from dotenv import load_dotenv
load_dotenv()
import json

logging.basicConfig(level=logging.INFO)

AI_MODEL = "tngtech/deepseek-r1t2-chimera:free"

# OpenRouter client (OpenAI-compatible)
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ.get("OPENROUTER_API_KEY"),

)

print("API key loaded:", os.environ.get("OPENROUTER_API_KEY"))


def rewrite_to_english(title: str, content: str):
    prompt = build_rewrite_prompt(title, content)

    try:
        resp = client.chat.completions.create(
            model=AI_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=3500,
        )

        raw = resp.choices[0].message.content
        data = json.loads(raw)

        english_title = data["title"]
        html_content = data["content"]

        logging.info("Rewrite succeeded")
        return english_title, html_content

    except Exception as e:
        logging.error(f"Rewrite failed: {e}")
        return None, f"<p>Rewrite failed: {e}</p>"



if __name__ == "__main__":
    # Choose ONE article id from your `articles` table to test
    original_article_id = 1

    row = get_article_by_id(original_article_id)
    if not row:
        print(f"No article found with id={original_article_id}")
        raise SystemExit(1)

    article_id, title_zh, content_zh = row

    print("Rewriting article:", article_id)

    english_title, html_en = rewrite_to_english(title_zh, content_zh)

    insert_rewritten_article(
        original_article_id=article_id,
        title=english_title,  # can improve later with English title
        content_html=html_en,
        ai_model=AI_MODEL
    )

    print("English rewrite saved to database.")

