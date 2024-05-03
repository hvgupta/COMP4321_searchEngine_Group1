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
from nltk.stem import PorterStemmer as Stemmer
import sqlite3
from itertools import chain
from collections import Counter


# To Harsh:
# The imports on the above are just for reference because they are copied from crawler.py
# Free to add more lib.
# Unless necessary, you are suggested not to add numpy as it may fuck up the project 😔
# Add oil OwO QwQ

# Create a list of stopwords
stopword = str(Path.cwd()) + '/files/stopwords.txt'

# Load database, then create a cursor.
path_of_db = str(Path.cwd()) + '/files/database.db'
connection = sqlite3.connect(path_of_db)
cursor = connection.cursor()

# Stemmer
ps = Stemmer()

# Open stopword
with open(stopword, 'r') as file:
    stopwords = file.read().split()


def parse_string(query: str):
    """
    Input: query: str: The string entered in the text box
    Return: Array of arrays, containing the word_id of the query word
    For example: [[1], [2,3]]
    Where [2,3] represents a phrase, while [1] represents a single query word.
    """

    # Create two arrays of phrases and words to be queried.
    phrases = [x.lower() for x in re.findall('"([^"]*)"', query) if x]
    single_word = [x.lower() for x in re.findall(r'''"[^"]*"|'[^']*'|\b([^\d\W]+)\b''', query) if x]

    # Remove every stopwords in the single_word as they are not necessary.
    # During the process we will also stem the word
    single_word_no_stopword = [ps.stem(x) for x in single_word if x not in stopwords]
    phrases_no_stopword = []

    # Remove every stopwords in the phrases as they are not necessary.
    # During the process we will also stem the word
    for phrase in phrases:
        querywords = phrase.split()

        resultwords = [ps.stem(word) for word in querywords if word.lower() not in stopwords]
        result = ' '.join(resultwords)

        phrases_no_stopword.append(result)

    # Create an array for returning later
    result = []

    # Put the converted single word phrase into result
    for element in single_word_no_stopword:
        word_id = cursor.execute("""
            SELECT word_id FROM word_id_word WHERE word = ? 
        """, (element,)).fetchone()[0]

        result.append([word_id])

    # Put the converted phrase into a list, then into result
    # Iterate over the phrases
    for element in phrases_no_stopword:
        list_of_word_id = []
        words = element.split()
        # Iterate over the word in the phrase
        for word in words:
            word_id = cursor.execute("""
                        SELECT word_id FROM word_id_word WHERE word = ? 
                    """, (word,)).fetchone()[0]
            list_of_word_id.append(word_id)

        result.append(list_of_word_id)

    return result


def search_engine(query: list):
    """
    Input:
    """

    # Create dummy search results list
    return {
        274824763: 100,
        1205567751: 99,
        920764120: 98,
        1438583588: 97,
        1490639970: 96,
        3598577144: 95,
        2259713099: 94,
        4188482033: 93,
        3498190479: 92,
        970995164: 91,
        2118143756: 90,
        1126196924: 89,
        1379349482: 88,
        3567468868: 87,
        536842977: 86,
        49979993: 85,
        3383128572: 84,
        1328677714: 83,
        2221854967: 82,
        1966629410: 81,
        3194270087: 80,
        684159280: 79,
        3818627733: 78,
        1695535163: 77,
        2924675998: 76,
        3008770854: 75,
        2013978755: 74,
        4271804973: 73,
        901923208: 72,
        3298095965: 71,
        264773880: 70,
        422538157: 69,
        3530799112: 68,
        1424476838: 67,
        2679838979: 66,
        2193500603: 65,
        1239611934: 64,
        3480651952: 63,
        69884693: 62,
        4118604224: 61,
        1042299493: 60,
        3210240025: 59,
        1946465212: 58,
        4069572882: 57,
        969675447: 56,
        617161231: 55,
        4019581354: 54,
        1761706756: 53,
        2724024481: 52,
        1393287796: 51
    }