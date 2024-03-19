import argparse
from socket import gaierror
import urllib.request
import urllib.parse
from urllib.parse import urljoin, urlparse
from typing import Tuple

from bs4 import BeautifulSoup as bsoup
import requests
import sqlite3
import re
import datetime
import dateutil.parser
from requests import Response


def get_soup(url: str) -> bsoup:
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

    return soup


def get_subpage_url(url: str) -> list:
    all_url = []
    asoup = get_soup(url)
    for anchor in asoup.findAll("a", href=True):
        href = anchor['href']
        if href != " " or href is not None:
            href = (urljoin(url, href))
            all_url.append(href)
    print(all_url)
    return all_url


def recursively_crawl(num_pages: int, url: str):
    pass


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

    get_subpage_url(url)

    recursively_crawl(num_pages, url)


if __name__ == '__main__':
    main()
