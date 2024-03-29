from urllib.parse import urljoin, urlparse
from zlib import crc32
from bs4 import BeautifulSoup as bsoup
import requests
import sqlite3
from email.utils import parsedate_to_datetime
from datetime import datetime
import re
import asyncio
from pathlib import Path
import signal
from contextlib import contextmanager

regex = re.compile('[^a-zA-Z]')

db_path = str(Path.cwd()) + '/src/files/database.db'

connection = sqlite3.connect(db_path)

cursor = connection.cursor()


class TimeoutException(Exception):
    pass


# Thanks https://stackoverflow.com/a/601168 for providing this function.
@contextmanager
def time_limit(seconds):
    def signal_handler(signum, frame):
        raise TimeoutException("Timed out!")

    signal.signal(signal.SIGALRM, signal_handler)
    signal.alarm(seconds)
    try:
        yield
    finally:
        signal.alarm(0)


async def get_soup(url: str) -> (bsoup, int, int, int):
    # We will skip pdf and mailto
    if url[-3:] == "pdf" or url[0:6] == "mailto":
        return bsoup(""), 0, 0, 0

    if "https://" not in url and "http://" not in url:
        url = "https://" + url

    # Try to get the data. If failed, then the program terminates.
    try:
        with time_limit(5):
            request = requests.get(url)
        statCode = request.status_code
        try:
            last_modif = parsedate_to_datetime((request.headers['last-modified']))
            last_modif = int(datetime.timestamp(last_modif))

        # If we cannot crawl the date, get the current time
        except KeyError:
            last_modif = parsedate_to_datetime((request.headers['Date']))
            last_modif = int(datetime.timestamp(last_modif))

    except TimeoutException:
        print("Crawling the page " + url + " exceed 5 second! Skipping crawling the page!")
        return bsoup(""), 0, 0, 408

    # Otherwise
    except:
        print("Error occurred when crawling the page " + url + ". Skipping")
        return bsoup(""), 0, 0, 500

    # Check if the request is successful or not.
    # If not then we assume the website is invalid, or the server is not responding.
    if statCode != -1:
        if statCode not in range(200, 399):
            print("Error code " + str(statCode) + " for webpage " + url + "!")
            return bsoup(""), 0, statCode
    else:
        print("Page crawling error for page " + url + "! Skipping")
        return bsoup(""), 0, 0, statCode

    response = request.text
    soup = bsoup(response, "lxml")

    # Try to get the size of the page
    try:
        size = request.headers['content-length']
    except KeyError:
        size = len(request.content)

    return soup, last_modif, size, statCode


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
    # If we did not pass the soup inside, due to crawling error, return a blank tuple
    if soup is None:
        return tuple()

    # Try to get the title of the website
    try:
        title = soup.title.get_text()
    # If one cannot get the title, just assign none to the title
    except AttributeError:
        title = ""

    cur_url_parsed = urlparse(cur_url)
    cur_url_parsed = (cur_url_parsed.scheme + "://" + cur_url_parsed.netloc + cur_url_parsed.path)

    if parent_url is not None:
        par_url_parsed = urlparse(parent_url)
        par_url_parsed = (par_url_parsed.scheme + "://" + par_url_parsed.netloc + par_url_parsed.path)
    else:
        par_url_parsed = None

    cur_page_id = crc32(str.encode(cur_url_parsed))
    parent_page_id = crc32(str.encode(par_url_parsed)) if parent_url is not None else 0

    # Have to handle the <br> elements 🖕

    for br in soup.select("br"):
        br.replace_with("\n")

    text = soup.get_text().split()  # get list of strings

    for i in range(len(text)):
        text[i] = re.sub("[^a-zA-Z]+", "", text[i]).lower()

    while "" in text:
        text.remove("")

    page_id_text = list(zip([cur_page_id] * len(text), text))

    return cur_page_id, parent_page_id, title, cur_url_parsed, last_modif, page_id_text


def recursively_crawl(num_pages: int, url: str):
    count = 0
    queue = []  # Queue for BFS
    parent_links = []
    canBreak = 0
    is_init = 1

    visited = []  # Visited pages

    queue.append(url)

    # num_pages > 0: To ensure we are in the limit
    # queue != []: To ensure the website still have sub-links.
    while num_pages > 0 and queue != [] and canBreak == 0:

        count += 1

        cur_url = queue.pop(0)

        if count != 1:
            par_link = parent_links.pop(0)
        else:
            par_link = None

        visited.append(cur_url)

        soup, last_modif, size, stat = asyncio.run(get_soup(cur_url))

        parent_link = cur_url

        all_url = get_sub_link(cur_url, soup)

        for url in all_url:
            # Ensuring that cycles does not exist.
            if url not in visited and url not in queue:
                queue.append(url)
                parent_links.append(parent_link)
            elif url in visited:
                insert_data_into_relation(crc32(str.encode(url)), crc32(str.encode(parent_link)))
                connection.commit()

        cur_page_id, parent_page_id, title, cur_url_parsed, last_modif, text = (
            get_info(cur_url, soup, last_modif, par_link))

        # If the statCode is 0 (i.e. The website returns nothing), or error code falls into [400, 499] (Error)
        if stat == 0 or stat in range(400, 499):
            insert_data_into_relation(int(cur_page_id), int(parent_page_id))
            insert_data_into_page_info(cur_page_id, size, last_modif, title)
            insert_data_into_id_url(cur_page_id, cur_url)
            connection.commit()
            continue

        # If the database has the exact item (Which is page_id), and the last modification date is newer / the same
        # as the crawled date, skip adding to database.
        result = cursor.execute("""
            SELECT * FROM page_info WHERE page_id=?
        """, (cur_page_id,))

        fetch1 = result.fetchone()

        if fetch1 is not None:
            # Not a valid page
            if fetch1[2] is None and last_modif is None:
                continue
            # If the date of last modification is older
            if fetch1[2] >= last_modif:
                canBreak = 1
                print("Page crawling has been completed before! Skip crawling.")
                if is_init:
                    break
                else:
                    continue
            else:
                # Delete the original data, then insert new data
                cursor.execute("DELETE FROM relation WHERE parent_id = ?", (cur_page_id,))
                cursor.execute("DELETE FROM page_id_word WHERE page_id = ?", (cur_page_id,))
                cursor.execute("DELETE FROM page_info WHERE page_id = ?", (cur_page_id,))
                cursor.execute("DELETE FROM title_page_id_word WHERE page_id = ?", (cur_page_id,))
                insert_data_into_relation(int(cur_page_id), int(parent_page_id))
                insert_data_into_page_info(cur_page_id, size, last_modif, title)
                insert_data_into_page_id_word(text)
                insert_data_into_title_page_id_word(title, cur_page_id)
                connection.commit()
                is_init = 0
                num_pages -= 1
                continue

        insert_data_into_relation(int(cur_page_id), int(parent_page_id))
        insert_data_into_page_info(cur_page_id, size, last_modif, title)
        insert_data_into_id_url(cur_page_id, cur_url)
        insert_data_into_page_id_word(text)
        insert_data_into_title_page_id_word(title, cur_page_id)
        connection.commit()
        is_init = 0
        num_pages -= 1
    connection.commit()


def insert_data_into_relation(child, parent):
    # Assume the database has been created
    cursor.execute("""
        INSERT INTO relation VALUES (?,?)
    """, (child, parent))


def insert_data_into_id_url(page_id, url):
    cursor.execute("""
        INSERT INTO id_url VALUES (?,?)
    """, (page_id, url))


def insert_data_into_page_info(page_id, size, last_modif, title):
    cursor.execute("""
        INSERT INTO page_info VALUES (?,?,?,?)
    """, (page_id, size, last_modif, title))


def insert_data_into_page_id_word(list_of_id):
    cursor.executemany("""
        INSERT INTO page_id_word VALUES (?,?)
        """, list_of_id)


def insert_data_into_title_page_id_word(title, page_id):
    title = title.split()

    for i in range(len(title)):
        title[i] = re.sub("[^a-zA-Z]+", "", title[i])

    while "" in title:
        title.remove("")

    new_list = zip([page_id] * len(title), title)

    cursor.executemany("""
        INSERT INTO title_page_id_word VALUES (?,?)
        """, new_list)
