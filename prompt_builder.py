def build_rewrite_prompt(title: str, content: str) -> str:
    return f"""
You are an English-language financial journalist.

Rewrite the following Chinese financial news article.

Requirements:
1. Generate a concise, professional English news headline.
2. Rewrite the article into fluent, neutral, professional English.
3. DO NOT translate literally — rewrite based on meaning.
4. Preserve all facts, numbers, and entities.
5. Use a Western news structure.
6. Add 1–2 short paragraphs of original analysis or global context.
7. Return output in STRICT JSON format exactly as follows:

{{
  "title": "English headline here",
  "content": "<p>HTML paragraph 1</p><p>HTML paragraph 2</p>"
}}

Rules:
- Use ONLY <p> tags in content
- Do NOT use Markdown
- Do NOT include explanations outside JSON

-------------------------------
【原始中文标题】
{title}

【原始中文正文】
{content}
-------------------------------
"""

def save_prompt(prompt: str, filename: str = "rewrite_prompt.txt"):
    with open(filename, "w", encoding="utf-8") as f:
        f.write(prompt)