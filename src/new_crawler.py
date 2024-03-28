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


async def info_crawler():
    pass
