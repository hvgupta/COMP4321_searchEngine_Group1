import argparse
from datetime import datetime
import sqlite3
from itertools import chain
import time

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
              page_id INTEGER,
              word TEXT
            )""")

        connection.commit()

    except sqlite3.OperationalError:
        # Table created. Pass creating.
        pass


def create_file_from_db():
    with open("spider_result.txt", "w+") as file:
        try:
            cursor.execute("""
                SELECT page_id FROM page_info  
            """)
        except sqlite3.OperationalError:
            print("You did not create the necessary databases yet. Crawling with default setting.")
            from src.crawler import recursively_crawl
            from src.indexer import indexer
            init_database()
            recursively_crawl(num_pages=30, url="https://www.cse.ust.hk/~kwtleung/COMP4321/testpage.htm")
            indexer()
            create_file_from_db()

        all_page_id = cursor.fetchall()

        for pid in list(chain.from_iterable(all_page_id)):
            pageinfo = cursor.execute("""
                SELECT * FROM page_info WHERE page_id = ?
            """, (pid,)).fetchone()

            url = cursor.execute("""
                    SELECT url FROM id_url WHERE page_id = ?
                """, (pid,)).fetchone()[0]

            file.write(pageinfo[3])
            file.write("\n")
            file.write(url)
            file.write("\n")

            file.write(str(datetime.fromtimestamp(pageinfo[2])) + ", " + str(pageinfo[1]) + "\n")

            # Top 10 words
            list_of_word = cursor.execute("""
                SELECT word, Count(word) AS Frequency
                FROM page_id_word
                WHERE page_id = ?
                GROUP BY word
                ORDER BY
                    Frequency DESC
                 """, (pid,)).fetchall()

            number = 0

            for word in list_of_word:
                if number > 9:
                    break
                keyword = word[0]  # Unpack the word
                count = word[1]

                if keyword in stopwords:
                    continue

                file.write(keyword + " " + str(count) + "; ")
                number = number + 1

            file.write("\n")

            # Child link
            list_of_child_id = cursor.execute("""
                SELECT child_id FROM relation WHERE parent_id = ? limit 10
            """, (pid,)).fetchall()

            list_of_child_id = list(chain.from_iterable(list_of_child_id))

            for i in range(len(list_of_child_id)):
                child_link = cursor.execute("""
                SELECT url FROM id_url WHERE page_id = ?
            """, (list_of_child_id[i],)).fetchone()[0]

                file.write(child_link + "\n")
            file.write("-" * 30 + "\n")


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument("-n", "--num", dest="NUM_PAGES", default="30",
                        help="Number of pages that will be crawled / indexed")
    parser.add_argument("-u", "--url", dest="URL", default="https://www.cse.ust.hk/~kwtleung/COMP4321/testpage.htm",
                        help="The URL that the program will be crawled")
    parser.add_argument("-t", "--test", dest="is_test", action='store_true', required=False,
                        help="Read the database and generate output")

    args = parser.parse_args()

    # Simply replace them with your own URL if you find passing flags into program is complicated.
    # - Number of pages that will be crawled / indexed - 
    MAX_NUM_PAGES = int(args.NUM_PAGES)

    # - The URL that the program will be crawled -
    URL = args.URL

    start_time = time.time()
    if not args.is_test:
        from src.crawler import recursively_crawl
        from src.indexer import indexer
        init_database()
        recursively_crawl(num_pages=MAX_NUM_PAGES, url=URL)
        indexer()
    else:
        create_file_from_db()
    print("--- %s seconds ---" % (time.time() - start_time))


if __name__ == '__main__':
    main()
