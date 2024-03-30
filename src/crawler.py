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
from src.indexer import insertInfoInvIdxTable, insertInfoWordPosTable, insertInfoWordTable


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
    title = text = re.sub("[^a-zA-Z]+", " ", title)
    
    text:str
    try:
        text = website.get_text()
    except AttributeError:
        text = ""
    text = re.sub("[^a-zA-Z]+", " ", text)
    
    parentID:int = getWebsiteCRC(url)
    size:int = len(text.split())
    
    return parentID, title, size, text
    

def recursively_crawl(conn:sqlite3.Connection,num_pages: int, url: str):
    cursor:sqlite3.Cursor = conn.cursor()
    queue:list[str] = [url]  # Queue for BFS
    visited:list[str] = []  # Visited pages
    count:int = 0
    
    relationArrayTrack:list[list[str]] = []
    
    while (count < num_pages and len(queue) > 0):
        
        cur_url = queue.pop(0)
        count += 1
        visited.append(cur_url)
        
        try:
            soup, last_modif = asyncio.run(get_soup(cur_url))
        except TypeError:
            return
        
        child_urls:list[str] = get_sub_link(cur_url, soup)
        child_urls:list[str] = list(set(child_urls))
        
        parentID, title, size, body = getInfo(soup,cur_url)
        
        fetch = cursor.execute("SELECT * FROM page_info WHERE page_id=?", (parentID,)).fetchall()
        
        if len(fetch) > 0 and fetch[0][2] >= last_modif:
            continue
        elif (len(fetch) > 0):
            #delete the original data, and then reinsert the new data
            sqlAPI.delete_from_table(conn, "relation", {"parent_id":parentID})

        sqlAPI.insertIntoTable(cursor, "page_info", [parentID, size, last_modif, title])
        sqlAPI.insertIntoTable(cursor, "id_url", [parentID, cur_url])
        insertInfoWordTable(cursor, body)
        insertInfoWordTable(cursor, title)
        insertInfoInvIdxTable(cursor, parentID,"body",body)
        insertInfoInvIdxTable(cursor,parentID, "title",title)
        insertInfoWordPosTable(cursor, parentID, body, "body")
        insertInfoWordPosTable(cursor, parentID, title, "title")
        
        conn.commit()
        
        for url in child_urls:
            
            relationArrayTrack.append([getWebsiteCRC(url),parentID ])
            
            if url not in visited and url not in queue:
                queue.append(url)
        
    sqlAPI.insertIntoTable(cursor, "relation", relationArrayTrack)
    conn.commit()
