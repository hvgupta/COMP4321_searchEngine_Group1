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
stopword = str(Path.cwd()) + '/src/files/stopwords.txt'

# Load database, then create a cursor.
path_of_db = str(Path.cwd()) + '/src/files/database.db'
connection = sqlite3.connect(path_of_db, check_same_thread=False)  # Set check_same_thread to False because Flask initialized the connection in a different thread, this is safe because the search engine is read only
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
        1205567751: 3,
        274824763: 786,
        920764120: 345,
        1438583588: 123,
        1490639970: 43,
        3598577144: 76,
        2259713099: 54,
        4188482033: 89,
        3498190479: 45,
        970995164: 67,
        2118143756: 23,
        1126196924: 767,
        1379349482: 435,
        3567468868: 234,
        536842977: 675,
        49979993: 543,
        3383128572: 87,
        1328677714: 11,
        2221854967: 125,
        1966629410: 314,
        3194270087: 420,
        684159280: 99,
        3818627733: 100,
        1695535163: 164,
        2924675998: 890,
        3008770854: 999,
        2013978755: 911,
        4271804973: 534,
        901923208: 543,
        3298095965: 679,
        264773880: 679,
        422538157: 901,
        3530799112: 881,
        1424476838: 949,
        2679838979: 722,
        2193500603: 450,
        1239611934: 441,
        3480651952: 512,
        69884693: 256,
        4118604224: 129,
        1042299493: 946,
        3210240025: 871,
        1946465212: 800,
        4069572882: 708,
        969675447: 755,
        617161231: 245,
        4019581354: 347,
        1761706756: 432,
        2724024481: 555,
        1393287796: 666
    }