# Finance News Crawler (Local Prototype)

## Overview

This project is a **local end-to-end prototype** for crawling Chinese financial news articles, processing them, rewriting content into English using an LLM, and storing results in a MySQL database.

The purpose of this project was to:
- Validate crawling logic independently
- Design a clean, date-based batch crawling mechanism
- Build a full ingestion → processing → persistence pipeline
- Serve as a foundation before integrating into a larger team system

This repository represents the **standalone version** developed prior to team integration.

---

## Supported Data Sources

- **Eastmoney (东方财富)**
  - Article list API
  - Date-based pagination
  - Article page parsing
- (CLS logic was later handled in the team repository)

---

## Project Structure
finance_crawler/
├── crawl.py # Entry point for date-based batch crawling
├── db.py # Database connection & insert/query helpers
├── rewrite.py # LLM-based Chinese → English rewriting
├── prompt_builder.py # Prompt construction for rewriting
├── generate_prompt.py # Utilities for prompt generation
├── outputs/
├── article_zh.txt # Optional local output for debugging
├── .env # Environment variables (DB credentials, API keys)
├── README.md
└── requirements.txt


---

## Core Workflow

1. **Fetch article list**
   - Uses Eastmoney list API
   - Pages sorted by publish time (newest first)

2. **Date-based filtering**
   - Skip articles newer than target date
   - Process only articles matching target date
   - Stop pagination once older articles are reached

3. **Article crawling**
   - Fetch article HTML
   - Parse title, content, publish time, and source

4. **Deduplication**
   - Check database by `url`
   - Skip existing articles

5. **Persistence**
   - Store original Chinese article in MySQL
   - Record crawl time and publish time

6. **Optional rewriting**
   - Generate structured English HTML using LLM
   - Store rewritten content in a separate table


## How Date-Based Crawling Works

The crawler is designed to be **efficient and deterministic**:

- Articles are fetched page by page (newest → oldest)
- For each article:
  - `publish_date > target_date` → skip
  - `publish_date == target_date` → crawl & save
  - `publish_date < target_date` → stop crawling entirely

This avoids unnecessary requests and guarantees correctness.

---

## How Date-Based Crawling Works

The crawler is designed to be **efficient and deterministic**:

- Articles are fetched page by page (newest → oldest)
- For each article:
  - `publish_date > target_date` → skip
  - `publish_date == target_date` → crawl & save
  - `publish_date < target_date` → stop crawling entirely

This avoids unnecessary requests and guarantees correctness.

---

