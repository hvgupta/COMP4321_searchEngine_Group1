from urllib.parse import urljoin, urlparse
from zlib import crc32
import requests
import sqlite3
from email.utils import parsedate_to_datetime
from datetime import datetime
import re
import asyncio
from pathlib import Path
import math

# To Harsh:
# The imports on the above are just for reference because they are copied from crawler.py
# Free to add more lib.
# Unless necessary, you are suggested not to add numpy as it may fuck up the project 😔
# Add oil OwO QwQ

# Create a list of stopwords
stopword = str(Path.cwd()) + '/files/stopwords.txt'

with open(stopword, 'r') as file:
    stopwords = file.read().split()


def parse_string(query: str):
    """
    Input: query: str: The string entered in the text box
    Return: Two arrays (Tuple), the first one are words that are quoted (phrase),
            while the second one are the words that are not quoted (words)
    """

    # Create two arrays of phrases and words to be queried.
    phrases = [x.lower() for x in re.findall('"([^"]*)"', query) if x]
    single_word = [x.lower() for x in re.findall(r'''"[^"]*"|'[^']*'|\b([^\d\W]+)\b''', query) if x]

    # Remove every stopwords in the single_word as they are not necessary.
    single_word_no_stopword = [x for x in single_word if x not in stopwords]
    phrases_no_stopword = []

    # Remove every stopwords in the phrases as they are not necessary.
    for phrase in phrases:
        querywords = phrase.split()

        resultwords = [word for word in querywords if word.lower() not in stopwords]
        result = ' '.join(resultwords)

        phrases_no_stopword.append(result)

    print(phrases_no_stopword)
    print(single_word_no_stopword)




