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

class Crawler:

    def __init__(self):
