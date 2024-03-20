import argparse
from socket import gaierror
import urllib.request
import urllib.parse
from urllib.parse import urljoin, urlparse
from typing import Tuple
import asyncio
from zlib import crc32


from bs4 import BeautifulSoup as bsoup
import requests
import sqlite3
import re
import datetime
import dateutil.parser
from requests import Response


''' Check the validity of URL, fix the URL if necessary. Get the content of the URL.

Args:
    url (str): The URL that we want to get soup from

Returns:
    tuple: return back the fixed URL, and also the bsoup object of the fetched URL
'''
def get_soup(url: str) -> tuple[str, bsoup]:
    if "https://" not in url and "http://" not in url:
        newURL = "http://" + url
    else:
        newURL = url

    try:
        request = requests.get(newURL)
        statCode = request.status_code
    except gaierror:
        print("URL provided is not valid!")
        exit(255)

    # Check if the request is successful or not.
    # If not then we assume the website is invalid, or the server is not responding.
    if statCode not in range(200, 399):
        print("Error code " + str(statCode) + ". Please check your input and try again.")
        exit(255)

    response = request.text
    soup = bsoup(response, "html.parser")

    return newURL, soup


''' Get all the URLs of the page.

Args:
    url (str): The url of the page
    soup (bsoup): The soup object of the page

Returns:
    list: list of all URLs of the page
'''
def get_subpage_url(url:str, soup: bsoup) -> list:
    all_url = []
    asoup = soup
    for anchor in asoup.findAll("a", href=True):
        href = anchor['href']
        if href != " " or href is not None:
            href = urlparse(urljoin(url, href))
            href = (href.scheme + "://" + href.netloc + href.path)
            all_url.append(href)
    print(all_url)
    return all_url


''' Get the info of the pages, including titles, page_ids, ...

Args:
    url (str): The url of the page
    soup (bsoup): The soup object of the page

Returns:
    list: list of all required data.
'''
def get_info_from_page(url, soup:bsoup) -> dict:
    info = {}
    title = soup.title.get_text()
    print(title)
    last_modif = soup.find("meta")
    print(last_modif)
    
    page_id = crc32(url)


''' Insert data into the database.

Args:
    data (tuple): tuples of all necessary data
'''
def add_data_into_database(title: str, url: str, page_id: int, ):
    connection = sqlite3.connect('mydatabase.db')
    cursor = connection.cursor()




''' Insert data into the database.

Args:
    num_pages (int): Number of pages to be crawled
    url (str): The url of the page
    url_array: For recursion use only. Must not pass anything into it

Returns:
    None
'''
def recursively_crawl(num_pages: int, url: str, url_array = []):
    while num_pages > 0:
        return
    return

    


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


if __name__ == '__main__':
    main()
