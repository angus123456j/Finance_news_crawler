
# import os to read .env file
import os
# import logging for debugging
import logging

from openai import OpenAI
# imports functions from db.py and prompt_builder.py
from db import get_article_by_id, insert_rewritten_article
from prompt_builder import build_rewrite_prompt


# load_dotenv
# → Reads a .env file and injects values into environment variables
from dotenv import load_dotenv
load_dotenv()

import json

logging.basicConfig(level=logging.INFO)

# LLM model routed via OpenRouter (OpenAI-compatible API)
AI_MODEL = "tngtech/deepseek-r1t2-chimera:free"

# OpenRouter client (OpenAI-compatible)
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv.get("OPENROUTER_API_KEY"),

)

#print("API key loaded:", os.getenv.get("OPENROUTER_API_KEY"))


def rewrite_to_english(title: str, content: str):
    """
    Rewrite a Chinese article into English using an LLM.

    Inputs:
    - title (str): Original Chinese title
    - content (str): Original Chinese article body

    Returns:
    - (english_title, html_content) on success
    - (None, error_html) on failure
    """

    # Build a structured prompt that instructs the LLM how to rewrite
    # This usually includes tone, format, and output constraints
    prompt = build_rewrite_prompt(title, content)

    try:
        # Send a chat completion request to the LLM
        # NOTE:
        # - client is OpenAI-compatible, but the model may be DeepSeek via OpenRouter
        # - messages must follow the chat format (role + content)
        resp = client.chat.completions.create(
            model=AI_MODEL,                  # Which LLM to use
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,                 # Controls creativity (0 = deterministic)
            max_tokens=3500,                 # Cap output length to avoid runaway responses
        )

        # Extract the raw text returned by the model
        # The model is expected to return JSON as a string
        raw = resp.choices[0].message.content

        # Parse the JSON output produced by the LLM
        # Expected schema:
        # {
        #   "title": "...",
        #   "content": "<p>...</p>"
        # }
        data = json.loads(raw)

        # Extract rewritten English title
        english_title = data["title"]

        # Extract rewritten HTML-formatted article body
        html_content = data["content"]

        logging.info("Rewrite succeeded")

        return english_title, html_content

    except Exception as e:
        # Catch ALL failures:
        # - API errors
        # - JSON parsing errors
        # - Schema mismatches
        # - Network issues
        logging.error(f"Rewrite failed: {e}")

        # Return safe fallback HTML so downstream code does not crash
        return None, f"<p>Rewrite failed: {e}</p>"


if __name__ == "__main__":
    """
    Standalone test runner for the rewrite pipeline.

  
    1. Fetch an existing Chinese article from the database
    2. Rewrite it into English using the LLM
    3. Store the rewritten result back into the database

    This is primarily for local testing / validation.
    """

    # Choose ONE article id from your `articles` (or sf_source_article) table
    # This should already exist in the database
    original_article_id = 1

    # Fetch the original article from the database
    # Expected return format:
    # (article_id, title_zh, content_zh)
    row = get_article_by_id(original_article_id)

    # Defensive check: ensure the article exists
    if not row:
        print(f"No article found with id={original_article_id}")
        raise SystemExit(1)

    article_id, title_zh, content_zh = row

    print("Rewriting article:", article_id)

    # Call the LLM rewrite function
    # This converts Chinese → English + HTML
    english_title, html_en = rewrite_to_english(title_zh, content_zh)

    # Persist the rewritten article to the database
    # This creates a new row linked to the original article
    insert_rewritten_article(
        original_article_id=article_id,  # Foreign key reference
        title=english_title,              # English title
        content_html=html_en,             # HTML body
        ai_model=AI_MODEL                 # Record which model produced this rewrite
    )

    print("English rewrite saved to database.")
