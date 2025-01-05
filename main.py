import os
import sqlite3
import time

try:
    os.remove("./src/files/database.db")
except:
    pass

connection = sqlite3.connect('./src/files/database.db')

with open("./src/files/stopwords.txt", 'r') as file:
    stopwords = file.read().split()

cursor = connection.cursor()


# Init a database, when there is a conflict, we IGNORE those contents
def init_database():
    try:
        cursor.execute("""
            CREATE TABLE relation (
                child_id INTEGER [primary key], 
                parent_id INTEGER
            )""")

        cursor.execute("""
            CREATE TABLE id_url (
                page_id INTEGER [primary key],
                url TEXT [primary key],
                UNIQUE (page_id, url) ON CONFLICT IGNORE
            )""")

        cursor.execute("""
            CREATE TABLE word_id_word (
                word_id INTEGER [primary key],
                word TEXT [primary key],
                UNIQUE (word_id, word) ON CONFLICT IGNORE 
            )""")

        cursor.execute("""
            CREATE TABLE inverted_idx (
              page_id INTEGER,
              word_id INTEGER,
              count INTEGER, 
              UNIQUE (page_id, word_id, count) ON CONFLICT IGNORE
            )""")

        cursor.execute("""
            CREATE TABLE title_inverted_idx (
              page_id INTEGER,
              word_id INTEGER,
              count INTEGER,
              UNIQUE (page_id, word_id, count) ON CONFLICT IGNORE
            )""")

        cursor.execute("""
            CREATE TABLE page_info (
              page_id INTEGER [primary key],
              size INTEGER,
              last_mod_date INTEGER,
              title TEXT,
              UNIQUE (page_id, size, last_mod_date, title) ON CONFLICT IGNORE
            )""")

        cursor.execute("""
            CREATE TABLE page_id_word (
              seq INTEGER,
              page_id INTEGER,
              word TEXT
            )""")

        cursor.execute("""
            CREATE TABLE page_id_word_stem (
              page_id INTEGER,
              word TEXT
            )""")

        cursor.execute("""
            CREATE TABLE title_page_id_word_stem (
              page_id INTEGER,
              word TEXT
            )""")

        cursor.execute("""
            CREATE TABLE title_page_id_word (
              seq INTEGER,
              page_id INTEGER,
              word TEXT
            )""")

        cursor.execute("""
            CREATE TABLE title_forward_idx (
              word_id INTEGER,
              count INTEGER,
              UNIQUE (word_id, count) ON CONFLICT REPLACE
        )""")

        cursor.execute("""
            CREATE TABLE forward_idx (
              word_id INTEGER,
              count INTEGER
        )""")
        
        cursor.execute("""
            CREATE TABLE page_rank (
              page_id INTEGER [primary key],
              score REAL
        )""")

        connection.commit()

    except sqlite3.OperationalError:
        # Table created. Pass creating.
        pass


def create_file_from_db():
    from src.crawler import recursively_crawl
    from src.crawler import closeCrawler
    from src.indexer import indexer
    init_database()
    recursively_crawl(num_pages=300, url="https://www.cse.ust.hk/~kwtleung/COMP4321/testpage.htm")
    closeCrawler()
    indexer()


def main():
    start_time = time.time()
    create_file_from_db()
    print("--- %s seconds for creating database ---" % (time.time() - start_time))
    connection.close()
    os.system("flask run")


if __name__ == '__main__':
    main()
