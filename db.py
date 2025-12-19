# mysql.connector
# → Official MySQL driver for Python
# → Lets Python talk to a MySQL database over TCP
import mysql.connector


# datetime
# → Used to timestamp when articles are parsed or rewritten
from datetime import datetime


# os
# → Lets you read environment variables (os.getenv)
import os

# load_dotenv
# → Reads a .env file and injects values into environment variables
from dotenv import load_dotenv

load_dotenv()  # loads variables from .env into environment


# What this function does
# This is a connection factory:
# Every DB operation calls this
# Each call creates a fresh connection
# Why this is good design
# Connections are short-lived
# No shared global state
# Safe for scripts & cron jobs
# Avoids stale connections
def get_db_connection():
    conn = mysql.connector.connect(
        host=os.getenv("DB_HOST", "localhost"),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", ""),
        database=os.getenv("DB_NAME", "news_data"),
        port=int(os.getenv("DB_PORT", "3306")),
    )
    return conn


# This is the entry point of the crawler into the database.
def insert_article(source, url, title, content, article_time):

    # Opens a new DB connection
    # Creates a cursor
    # dictionary=True → results returned as dicts instead of tuples
    conn = get_db_connection()
    cursor = conn.cursor(dictionary= True)

    sql = """
    INSERT INTO articles (source, url, title, content, article_time, parse_time)
    VALUES (%s, %s, %s, %s, %s, %s)
    """

    # parse_time is the current time
    parse_time = datetime.now()

    # bings all values to SQL table
    values = (source, url, title, content, article_time, parse_time)

    

    # Executes the insert
    # Commits transaction so it’s permanent
    cursor.execute(sql, values)
    conn.commit()

    # closes connection
    cursor.close()
    conn.close()

    # debugg print line
    # print("Inserted into MySQL successfully.")

# fetches an article by its id
def get_article_by_id(article_id: int):

    # creates a db connection
    conn = get_db_connection()
    # creates a cursor
    cursor = conn.cursor()

    # cursor executes this command
    cursor.execute(
        "SELECT id, title, content FROM articles WHERE id = %s",
        (article_id,)
    )

    # Returns one row
    # None if no article exists
    row = cursor.fetchone()

    # closes cursor and connection
    cursor.close()
    conn.close()

    # reutrn the retrieved row
    return row


# function that insert the rewrittten article into the rewritten_article database
def insert_rewritten_article(original_article_id, title, content_html, ai_model):

    # creates db connection and cursor
    conn = get_db_connection()
    cursor = conn.cursor()

    # sql command that will insert the required fields
    sql = """
    INSERT INTO rewritten_articles
      (original_article_id, title, content, rewrite_time, ai_model)
    VALUES (%s, %s, %s, %s, %s)
    """

    # rewirte_time will be the current date
    rewrite_time = datetime.now()

    # cursor executes the insert
    cursor.execute(sql, (
        original_article_id,
        title,
        content_html,
        rewrite_time,
        ai_model
    ))

    # commits changes so its permenant
    conn.commit()

    # closes the cursor and the database connection
    cursor.close()
    conn.close()



# funciton to check if the article exists
def article_exists(url: str) -> bool:
    # creates db connection and cursor
    conn = get_db_connection()
    cursor = conn.cursor()

    # sql command to check if there are duplicates for the specific url
    sql = "SELECT 1 FROM articles WHERE url = %s LIMIT 1"
    # cursor executes this command
    cursor.execute(sql, (url,))

    # exists is a boolean value
    exists = cursor.fetchone() is not None

    # closes cursor and connection
    cursor.close()
    conn.close()

    return exists
