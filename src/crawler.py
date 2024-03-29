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
import src.sqlAPI as sqlAPI
import signal
from contextlib import contextmanager
from src.indexer import insertInfoInvIdxTable

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


async def get_soup(url: str) -> (bsoup, str):
    # We will skip pdf and mailto
    if url[-3:] == "pdf" or url[0:6] == "mailto":
        return

    if "https://" not in url and "http://" not in url:
        url = "https://" + url

    # Try to get the data. If failed, then the program terminates.
    try:
        # with time_limit(10):
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
        return

    # Otherwise
    except:
        print("Error occurred when crawling the page " + url + ". Skipping")
        return

    # Check if the request is successful or not.
    # If not then we assume the website is invalid, or the server is not responding.
    if statCode != -1:
        if statCode not in range(200, 399):
            print("Error code " + str(statCode) + " for webpage " + url + ". Please check your input and try again.")
            return
    else:
        print("Page crawling error for page " + url + "! Skipping")
        return

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
        text[i] = re.sub("[^a-zA-Z]+", "", text[i])

    while "" in text:
        text.remove("")

    size = soup.find("meta", attrs={"name": "size"})
    if size is None:
        size = len(text)

    page_id_text = list(zip([cur_page_id] * len(text), text))

    return cur_page_id, parent_page_id, title, cur_url_parsed, last_modif, size, page_id_text

def getWebsiteCRC(url:str)->int:
    urlParsed = urlparse(url)
    urlParsed = (urlParsed.scheme + "://" + urlParsed.netloc + urlParsed.path)
    return crc32(str.encode(urlParsed))

def getInfo(website:bsoup, url:str)->tuple[int, str, int, str]:
    
    if website is None:
        return tuple()
    
    title:str
    try:
        title = website.title.get_text()
    # If one cannot get the title, just assign none to the title
    except AttributeError:
        title = ""
    
    text:str
    try:
        text = website.get_text()
    except AttributeError:
        text = ""
    text = re.sub("[^a-zA-Z]+", " ", text)
    
    parentID:int = getWebsiteCRC(url)
    size:int = len(text.split())
    
    return parentID, title, size, text
    

def recursively_crawl1(num_pages: int, visited:list[str], queue:list[str]):
    
    if (len(queue) == 0):
        return
    count:int = 0
    
    relationArrayTrack:list[list[str]]
    
    while (count <= num_pages and len(queue) > 0):
        
        cur_url = queue.pop(0)
        visited.append(cur_url)
        
        try:
            soup, last_modif = asyncio.run(get_soup(cur_url))
        except TypeError:
            return
        
        child_urls:list[str] = get_sub_link(cur_url, soup)
        
        parentID, title, size, text = getInfo(soup,cur_url)
        
        fetch = cursor.execute("SELECT * FROM page_info WHERE page_id=?", (parentID,)).fetchone()
        
        if fetch is not None and fetch[2] >= last_modif:
            continue
        elif fetch is not None:
            #delete the original data, and then reinsert the new data
            sqlAPI.delete_from_table(cursor, "relation", {"parent_id":parentID})

        sqlAPI.insertIntoTable(cursor, "page_info", [parentID, size, last_modif, title])
        sqlAPI.insertIntoTable(cursor, "id_url", [parentID, cur_url])
        insertInfoInvIdxTable(cursor, soup, parentID,"body")
        insertInfoInvIdxTable(cursor, soup, parentID,"title")
        
        for url in child_urls:
            
            relationArrayTrack.append([parentID, getWebsiteCRC(url)])
            
            if url not in visited and url not in queue:
                queue.append(url)
                num_pages -= 1
        
    while(len(relationArrayTrack) > 0): sqlAPI.insertIntoTable(cursor, "relation", relationArrayTrack.pop(0))
    


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

        try:
            soup, last_modif = asyncio.run(get_soup(cur_url))
        except TypeError:
            continue

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
                
                
        sqlAPI.insertIntoTable(cursor, "relation", [cur_page_id, parent_page_id])
        sqlAPI.insertIntoTable(cursor, "page_info", [cur_page_id, size, last_modif, title])
        sqlAPI.insertIntoTable(cursor, "id_url", [cur_page_id, cur_url])
        sqlAPI.insertIntoTable(cursor, "page_id_word", text)
        sqlAPI.insertIntoTable(cursor, "title_page_id_word", [cur_page_id, title])
        is_init = 0
        connection.commit()
        num_pages -= 1


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
