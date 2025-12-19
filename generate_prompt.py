# imports two functions from prompt_builder.py
from prompt_builder import build_rewrite_prompt, save_prompt

# Load Chinese text from file
with open("outputs/article_zh.txt", "r", encoding="utf-8") as f:
    raw = f.read()
    

# Extract title + content
parts = raw.split("【正文】")
title = parts[0].replace("【标题】", "").strip()
content = parts[1].strip()

# Build and save prompt
prompt = build_rewrite_prompt(title, content)
#save_prompt(prompt, filename="outputs/rewrite_prompt.txt")

print("Rewrite prompt generated.")
