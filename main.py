import argparse
from datetime import datetime
import sqlite3
from itertools import chain
import pathlib

connection = sqlite3.connect(pathlib.Path(__file__).parent/'src/files/database.db')
connection.execute("PRAGMA foreign_keys = 1") # Enable foreign key, allowing for better retrieval of data.

cursor = connection.cursor()


def init_database():
    try:
        # the purpose of this table is to track the parent-child relationship between pages. (is done through link re-direction)
        cursor.execute("""
            CREATE TABLE relation (
                child_id INTEGER,
                parent_id INTEGER,
                PRIMARY KEY (child_id, parent_id), 
                FOREIGN KEY (child_id) REFERENCES page_info(page_id),
                FOREIGN KEY (parent_id) REFERENCES page_info(page_id)
            )""")

        # the purpose of this table is to ensure 2NF form
        cursor.execute("""
            CREATE TABLE id_url (
                page_id INTEGER,
                url TEXT UNIQUE,
                PRIMARY KEY (page_id),
                FOREIGN KEY (page_id) REFERENCES page_info(page_id)
            )""")

        # the purpose of this table is to create a map between word and its ID
        cursor.execute("""
            CREATE TABLE word_id_word (
                word_id INTEGER,
                word TEXT,
                PRIMARY KEY (word_id)
            )""")

        # this table is the inverted index for the body of the page
        cursor.execute("""
            CREATE TABLE inverted_idx (
                page_id INTEGER,
                word_id INTEGER,
                count INTEGER,
                PRIMARY KEY (page_id, word_id),
                FOREIGN KEY (page_id) REFERENCES page_info(page_id),
                FOREIGN KEY (word_id) REFERENCES word_id_word(word_id)
            )""")

        # this table is the inverted index for the title of the page
        cursor.execute("""
            CREATE TABLE title_inverted_idx (
                page_id INTEGER,
                word_id INTEGER,
                count INTEGER,
                PRIMARY KEY (page_id, word_id),
                FOREIGN KEY (page_id) REFERENCES page_info(page_id),
                FOREIGN KEY (word_id) REFERENCES word_id_word(word_id)
            )""")

        # the purpose of this table is to map the basic information about the page to its ID
        cursor.execute("""
            CREATE TABLE page_info (
                page_id INTEGER,
                size INTEGER,
                last_mod_date INTEGER,
                title TEXT,
                PRIMARY KEY (page_id)
            )""")

        cursor.execute("""
            CREATE TABLE page_id_word (
                page_id INTEGER,
                word TEXT,
                position INTEGER,
                PRIMARY KEY (position, word),
                FOREIGN KEY (page_id) REFERENCES page_info(page_id)
            )""")

        cursor.execute("""
            CREATE TABLE title_page_id_word (
                page_id INTEGER,
                word TEXT,
                position INTEGER,
                PRIMARY KEY (position, word),
                FOREIGN KEY (page_id) REFERENCES page_info(page_id)
            )""")

        connection.commit()

    except sqlite3.OperationalError:
        # Table created. Pass creating.
        pass


def create_file_from_db():
    with open("spider_result.txt", "w+") as file:
        cursor.execute("""
            SELECT page_id FROM page_info  
        """)

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

            # Child link
            list_of_child_id = cursor.execute("""
                SELECT child_id FROM relation WHERE parent_id = ?
            """, (pid,)).fetchall()

            list_of_child_id = list(chain.from_iterable(list_of_child_id))

            for i in range(len(list_of_child_id)):
                if i >= 10:
                    break

                child_link = cursor.execute("""
                SELECT url FROM id_url WHERE page_id = ?
            """, (list_of_child_id[i],)).fetchone()[0]

                file.write(child_link + "\n")
            file.write("-" * 30 + "\n")


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument("-n", "--num", dest="NUM_PAGES", default="30",
                        help="Number of pages that will be crawled / indexed")
    parser.add_argument("-u", "--url", dest="URL", default="https://comp4321-hkust.github.io/testpages/testpage.htm",
                        help="The URL that the program will be crawled")
    parser.add_argument("-t", "--test", dest="is_test", action='store_true', required=False,
                        help="Read the database and generate output")

    args = parser.parse_args()

    # Simply replace them with your own URL if you find passing flags into program is complicated.
    # - Number of pages that will be crawled / indexed - 
    MAX_NUM_PAGES = int(args.NUM_PAGES)

    # - The URL that the program will be crawled -
    URL = args.URL

    if not args.is_test:
        from src.crawler import recursively_crawl
        init_database()
        recursively_crawl(num_pages=MAX_NUM_PAGES, url=URL)

    else:
        create_file_from_db()


if __name__ == '__main__':
    main()
