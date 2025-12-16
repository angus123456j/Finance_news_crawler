import mysql.connector
from datetime import datetime

def get_db_connection():
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="",   # root has no password for homebrew setup
        database="news_data"
    )
    return conn

def insert_article(source, url, title, content, article_time):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary= True)

    sql = """
    INSERT INTO articles (source, url, title, content, article_time, parse_time)
    VALUES (%s, %s, %s, %s, %s, %s)
    """

    parse_time = datetime.now()

    values = (source, url, title, content, article_time, parse_time)

    cursor.execute(sql, values)
    conn.commit()

    cursor.close()
    conn.close()

    print("Inserted into MySQL successfully.")

def get_article_by_id(article_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, title, content FROM articles WHERE id = %s",
        (article_id,)
    )
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    return row

def insert_rewritten_article(original_article_id, title, content_html, ai_model):
    conn = get_db_connection()
    cursor = conn.cursor()

    sql = """
    INSERT INTO rewritten_articles
      (original_article_id, title, content, rewrite_time, ai_model)
    VALUES (%s, %s, %s, %s, %s)
    """

    from datetime import datetime
    rewrite_time = datetime.now()

    cursor.execute(sql, (
        original_article_id,
        title,
        content_html,
        rewrite_time,
        ai_model
    ))

    conn.commit()
    cursor.close()
    conn.close()

def article_exists(url: str) -> bool:
    conn = get_db_connection()
    cursor = conn.cursor()

    sql = "SELECT 1 FROM articles WHERE url = %s LIMIT 1"
    cursor.execute(sql, (url,))

    exists = cursor.fetchone() is not None

    cursor.close()
    conn.close()

    return exists
