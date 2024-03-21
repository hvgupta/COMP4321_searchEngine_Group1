from socket import gaierror
import urllib.request
from urllib.parse import urljoin, urlparse
import asyncio
from zlib import crc32
import pydoc

from bs4 import BeautifulSoup as bsoup
import requests
import sqlite3
import datetime
import dateutil.parser
import json

import indexer


def get_soup(url: str) -> bsoup:
    if "https://" not in url and "http://" not in url:
        url = "https://" + url

    # Try to get the data. If failed, then the program terminates.
    try:
        request = requests.get(url)
        statCode = request.status_code
    except gaierror:
        statCode = -1
        request = None
        print("Page crawling error! Skipping")
        pass

    # Check if the request is successful or not.
    # If not then we assume the website is invalid, or the server is not responding.
    if statCode is not -1:
        if statCode not in range(200, 399):
            print("Error code " + str(statCode) + ". Please check your input and try again.")
            exit(255)
    else:
        print("Page crawling error! Skipping")

    response = request.text
    soup = bsoup(response, "html.parser")

    return soup


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


def get_info(cur_url, soup, parent_url=None):
    if soup is None:
        return tuple()

    title = soup.title.get_text()

    cur_url_parsed = urlparse(cur_url)
    cur_url_parsed = (cur_url_parsed.scheme + "://" + cur_url_parsed.netloc + cur_url_parsed.path)

    page_id = crc32(cur_url_parsed)

    last_modif = soup.find("meta", attrs={"http-equiv": "last-modified"})
    if last_modif is None:  # Find the date of the website
        last_modif = soup.find("meta", attrs={"name": "date"})

    size = soup.find("meta", attrs={"name": "size"})
    if size is None:
        size = len(soup.find("body").text)


def insert_data_into_database(data: list):
    pass


def recursively_crawl(num_pages: int, url: str):
    pass
# Proposed: Using CRC32 to convert word into integer, and then use it as the primary key.
