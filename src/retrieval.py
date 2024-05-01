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