from urllib.parse import urljoin, urlparse
from zlib import crc32
import requests
import sqlite3
from email.utils import parsedate_to_datetime
from datetime import datetime
import re
import asyncio
from pathlib import Path

# To Harsh:
# The imports on the above are just for reference because they are copied from crawler.py
# Free to add more lib.
# Unless necessary, you are suggested not to add numpy as it may fuck up the project 😔
# Add oil OwO QwQ


def parse_string(query: str):
    """
    Input: query: str: The string entered in the text box
    Return: Two arrays (Tuple), the first one are words that are quoted (phrase),
            while the second one are the words that are not quoted
    """
    return (re.findall('"([^"]*)"', query)), [x for x in re.findall(r'''"[^"]*"|'[^']*'|\b([^\d\W]+)\b''', query) if x]


