from urllib.parse import urljoin, urlparse
from zlib import crc32
from bs4 import BeautifulSoup as bsoup
import requests
import sqlite3
from email.utils import parsedate_to_datetime
from datetime import datetime
import re

regex = re.compile('[^a-zA-Z]')

import indexer

connection = sqlite3.connect('files/database.db')

cursor = connection.cursor()

def init_database():
    try:
        cursor.execute("""
            CREATE TABLE relation (
                child_id INTEGER,
                parent_id INTEGER
            )""")

        cursor.execute("""
            CREATE TABLE id_url (
                page_id INTEGER,
                url TEXT
            )""")

        cursor.execute("""
            CREATE TABLE word_id_word (
                word_id INTEGER,
                word TEXT
            )""")

        cursor.execute("""
            CREATE TABLE inverted_idx (
              page_id INTEGER,
              word_id INTEGER,
              count INTEGER
            )""")

        cursor.execute("""
            CREATE TABLE page_info (
              page_id INTEGER,
              size INTEGER,
              last_mod_date INTEGER,
              title TEXT
            )""")

        cursor.execute("""
            CREATE TABLE page_id_word (
              page_id INTEGER,
              word TEXT
            )""")

        connection.commit()

    except sqlite3.OperationalError:
        # Table created. Pass creating.
        pass


def get_soup(url: str) -> (bsoup, str):
    last_modif = None
    if "https://" not in url and "http://" not in url:
        url = "https://" + url

    # Try to get the data. If failed, then the program terminates.
    try:
        request = requests.get(url)
        statCode = request.status_code
        last_modif = (request.headers['last-modified'])
        last_modif = parsedate_to_datetime(last_modif)
        last_modif = int(datetime.timestamp(last_modif))

    except KeyError:
        last_modif = None

    except:
        statCode = -1
        request = None
        print("Page crawling error! Skipping")
        pass

    # Check if the request is successful or not.
    # If not then we assume the website is invalid, or the server is not responding.
    if statCode != -1:
        if statCode not in range(200, 399):
            print("Error code " + str(statCode) + ". Please check your input and try again.")
            exit(255)
    else:
        print("Page crawling error! Skipping")

    response = request.text
    soup = bsoup(response, "lxml")

    return soup, last_modif


def get_sub_link(url, soup):
    if soup is None:
        return []

    all_url = []

    # Search for all tags with 'a'.
    for anchor in soup.findAll("a", href=True):

        # Obtain the link
        href = anchor['href']

        # If the link obtained is not blank
        if href != " " or href is not None:

            # Parse the url, so that we can get a better formatted url
            href = urlparse(urljoin(url, href))
            href = (href.scheme + "://" + href.netloc + href.path)

            # Try to remove last / if there exists
            if href[-1] == "/":
                href = href[:-1]

            # We can finally add the url into the list
            all_url.append(href)

    return all_url


def get_info(cur_url, soup, last_modif, parent_url=None):
    if soup is None:
        return tuple()

    title = soup.title.get_text()

    cur_url_parsed = urlparse(cur_url)
    cur_url_parsed = (cur_url_parsed.scheme + "://" + cur_url_parsed.netloc + cur_url_parsed.path)

    if parent_url is not None:
        par_url_parsed = urlparse(parent_url)
        par_url_parsed = (par_url_parsed.scheme + "://" + par_url_parsed.netloc + par_url_parsed.path)
    else:
        par_url_parsed = None

    cur_page_id = crc32(str.encode(cur_url_parsed))
    parent_page_id = crc32(str.encode(par_url_parsed)) if parent_url is not None else 0

    text = soup.find("body").text.split()

    for i in range(len(text)):
        text[i] = re.sub("[^a-zA-Z]+", "", text[i])

    while "" in text:
        text.remove("")

    size = soup.find("meta", attrs={"name": "size"})
    if size is None:
        size = len(text)

    page_id_text = list(zip([cur_page_id] * len(text), text))

    return cur_page_id, parent_page_id, title, cur_url_parsed, last_modif, size, page_id_text


def recursively_crawl(num_pages: int, url: str):
    count = 0
    queue = []  # Queue for BFS
    parent_links = []

    visited = []  # Visited pages

    queue.append(url)

    # num_pages > 0: To ensure we are in the limit
    # queue != []: To ensure the website still have sub-links.
    while num_pages > 0 and queue != []:

        count += 1

        cur_url = queue.pop(0)

        if count != 1:
            par_link = parent_links.pop(0)
        else:
            par_link = None

        visited.append(cur_url)

        soup, last_modif = (get_soup(cur_url))

        parent_link = cur_url

        all_url = get_sub_link(cur_url, soup)

        for url in all_url:
            # Ensuring that cycles does not exist.
            if url not in visited and url not in queue:
                queue.append(url)
                parent_links.append(parent_link)

        cur_page_id, parent_page_id, title, cur_url_parsed, last_modif, size, text = (
            get_info(cur_url, soup, last_modif, par_link))

        # If the database has the exact item (Which is page_id), and the last modification date is newer / the same
        # as the crawled date, skip adding to database.
        result = cursor.execute("""
            SELECT * FROM page_info WHERE page_id=?
        """, (cur_page_id,))

        fetch1 = result.fetchone()

        if fetch1 is not None:
            if fetch1[2] >= last_modif:
                num_pages -= 1
                continue
            else:
                pass

        insert_data_into_relation(int(cur_page_id), int(parent_page_id))
        insert_data_into_page_info(cur_page_id, size, last_modif,title)
        insert_data_into_id_url(cur_page_id, url)
        insert_data_into_page_id_word(text)
        num_pages -= 1


def insert_data_into_relation(child, parent):
    # Assume the database has been created
    cursor.execute("""
        INSERT INTO relation VALUES (?,?)
    """, (child, parent))
    connection.commit()


def insert_data_into_id_url(page_id, url):
    cursor.execute("""
        INSERT INTO id_url VALUES (?,?)
    """, (page_id, url))
    connection.commit()


def insert_data_into_page_info(page_id, size, last_modif, title):
    cursor.execute("""
        INSERT INTO page_info VALUES (?,?,?,?)
    """, (page_id, size, last_modif, title))
    connection.commit()


def insert_data_into_page_id_word(list_of_id):
    cursor.executemany("""
        INSERT INTO page_id_word VALUES (?,?)
        """, list_of_id)

    connection.commit()


def main():
    init_database()

    # - Number of pages that will be crawled / indexed -
    MAX_NUM_PAGES = 8

    # - The URL that the program will be crawled -
    URL = "https://comp4321-hkust.github.io/testpages/testpage.htm"

    recursively_crawl(MAX_NUM_PAGES, URL)


if __name__ == '__main__':
    main()
