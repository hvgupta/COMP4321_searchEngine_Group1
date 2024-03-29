import argparse
from datetime import datetime
import sqlite3
from itertools import chain
import pathlib
import time

connection = sqlite3.connect(pathlib.Path(__file__).parent/'src/files/database.db')
connection.execute("PRAGMA foreign_keys = 1") # Enable foreign key, allowing for better retrieval of data.

cursor = connection.cursor()


# Init a database, when there is a conflict, we IGNORE those contents
def init_database():
    try:
        # the purpose of this table is to track the parent-child relationship between pages. (is done through link re-direction)
        cursor.execute("""
            CREATE TABLE relation (
                child_id INTEGER,
                parent_id INTEGER,
                PRIMARY KEY (child_id, parent_id), 
                FOREIGN KEY (child_id) REFERENCES page_info(page_id) ON DELETE CASCADE,
                FOREIGN KEY (parent_id) REFERENCES page_info(page_id) ON DELETE CASCADE
            )""")

        # the purpose of this table is to ensure 2NF form
        cursor.execute("""
            CREATE TABLE id_url (
                page_id INTEGER,
                url TEXT UNIQUE,
                PRIMARY KEY (page_id),
                FOREIGN KEY (page_id) REFERENCES page_info(page_id) ON DELETE CASCADE
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
            CREATE TABLE body_inverted_idx (
                page_id INTEGER,
                word_id INTEGER,
                count INTEGER,
                PRIMARY KEY (page_id, word_id),
                FOREIGN KEY (page_id) REFERENCES page_info(page_id) ON DELETE CASCADE,
                FOREIGN KEY (word_id) REFERENCES word_id_word(word_id) ON DELETE CASCADE
            )""")

        # this table is the inverted index for the title of the page
        cursor.execute("""
            CREATE TABLE title_inverted_idx (
                page_id INTEGER,
                word_id INTEGER,
                count INTEGER,
                PRIMARY KEY (page_id, word_id),
                FOREIGN KEY (page_id) REFERENCES page_info(page_id) ON DELETE CASCADE,
                FOREIGN KEY (word_id) REFERENCES word_id_word(word_id) ON DELETE CASCADE
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
            CREATE TABLE body_page_id_word (
                word_id INTEGER,
                page_id INTEGER,
                position INTEGER,
                PRIMARY KEY (word_id, page_id),
                FOREIGN KEY (word_id) REFERENCES word_id_word(word_id) ON DELETE CASCADE,
                FOREIGN KEY (page_id) REFERENCES page_info(page_id) ON DELETE CASCADE
            )""")

        cursor.execute("""
            CREATE TABLE title_page_id_word (
                word_id INTEGER,
                page_id INTEGER,
                position INTEGER,
                PRIMARY KEY (word_id, page_id),
                FOREIGN KEY (word_id) REFERENCES word_id_word(word_id) ON DELETE CASCADE,
                FOREIGN KEY (page_id) REFERENCES page_info(page_id) ON DELETE CASCADE
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
                LIMIT 10 """, (pid,)).fetchall()

            for word in list_of_word:
                keyword = word[0]  # Unpack the word
                count = word[1]

                file.write(keyword + " " + str(count) + "; ")

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
        from src.crawler import recursively_crawl, recursively_crawl1
        from src.indexer import insertInfoInvIdxTable
        init_database()
        recursively_crawl1(num_pages=MAX_NUM_PAGES, url=URL)
        
    else:
        create_file_from_db()
    print("--- %s seconds ---" % (time.time() - start_time))


if __name__ == '__main__':
    main()
