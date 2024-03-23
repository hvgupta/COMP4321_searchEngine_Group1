from socket import gaierror
from urllib.parse import urljoin, urlparse
from zlib import crc32

from bs4 import BeautifulSoup as bsoup
import requests
import sqlite3
import datetime
import dateutil.parser
from dateutil import parser

import indexer


def get_soup(url: str) -> (bsoup, str):
    last_modif = None
    if "https://" not in url and "http://" not in url:
        url = "https://" + url

    # Try to get the data. If failed, then the program terminates.
    try:
        request = requests.get(url)
        statCode = request.status_code
        last_modif = (request.headers['last-modified'])

    except gaierror:
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
    parent_page_id = crc32(str.encode(par_url_parsed)) if parent_url is not None else None

    size = soup.find("meta", attrs={"name": "size"})
    if size is None:
        size = len(soup.find("body").text)

    return cur_page_id, parent_page_id, title, cur_url_parsed, last_modif, size


def recursively_crawl(num_pages: int, url: str):
    count = 0
    queue = []  # Queue for BFS
    parent_links = []

    visited = []  # Visited pages

    queue.append(url)

    while num_pages > 0:
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

        print(str(count), end=" ")
        print(get_info(cur_url, soup, last_modif, par_link))

        num_pages -= 1


def main():
    # - Number of pages that will be crawled / indexed -
    MAX_NUM_PAGES = 3

    # - The URL that the program will be crawled -
    URL = "https://comp4321-hkust.github.io/testpages/testpage.htm"

    recursively_crawl(MAX_NUM_PAGES, URL)


if __name__ == '__main__':
    main()
