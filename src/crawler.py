import argparse
from socket import gaierror
import urllib.request
import urllib.parse
from urllib.parse import urljoin, urlparse
from typing import Tuple
import asyncio
from zlib import crc32
import pydoc

from bs4 import BeautifulSoup as bsoup
import requests
import sqlite3
import re
import datetime
import dateutil.parser
from requests import Response


def parse_url(url: str) -> str:
    # If the beginning does not contains http:/, then we shall add one. 
    if "https://" not in url and "http://" not in url:
        new_url = "http://" + url
    else:
        new_url = url

    return new_url


def get_soup(url: str) -> bsoup:
    url = parse_url(url)

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
    if statCode != None:
        if statCode not in range(200, 399):
            print("Error code " + str(statCode) + ". Please check your input and try again.")
            exit(255)
    else:
        print("Page crawling error! Cannot handle the request of the page " + newURL + ". Skipping.")

    response = request.text
    soup = bsoup(response, "html.parser")

    return soup


def get_subpage_url(url: str, soup: bsoup) -> list:
    if soup == None:
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


def get_info_from_page(url, soup: bsoup, parent_url=None) -> list:
    if soup == None:
        return []

    info = []

    title = soup.title.get_text()

    print(title)
    last_modif = soup.find("meta")
    print(last_modif)
    page_id = crc32(url)
    parent_page_id = crc32(parent_url)


def extractWords(soup: bsoup):
    if soup == None:
        return []

    return soup.find("body").text.strip().split()


def add_data_into_database(data: list):
    ''' Insert data into the database.

    Args:
        data (tuple): tuples of all necessary data
    '''
    connection = sqlite3.connect('mydatabase.db')
    cursor = connection.cursor()


def recursively_crawl(num_pages: int, url: str):
    queue = []

    queue.append(url)

    while num_pages > 0:
        for count in range(len(queue)):
            current_url = queue.pop(0)


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument("-n", "--num_pages", dest="num_pages", default="30",
                        help="Number of pages that will be crawled / indexed")
    parser.add_argument("-u", "--url", dest="url", default="https://comp4321-hkust.github.io/testpages/testpage.htm",
                        help="The URL that the program will be crawled")

    args = parser.parse_args()

    # Simply replace them with your own URL if you find passing flags into program is complicated.
    # - Number of pages that will be crawled / indexed -
    num_pages = args.num_pages

    # - The URL that the program will be crawled -
    url = args.url

    url, soup = get_soup(url)

    subpage_urls = {url: get_subpage_url(url, soup)}  # Dict: parent link: child link

    print(subpage_urls)


if __name__ == '__main__':
    main()
