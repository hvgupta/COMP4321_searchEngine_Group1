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
connection = sqlite3.connect('path_of_db')
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
        """, element).fetchone()

        result.append([word_id if word_id is not None else -1])

    # Put the converted phrase into a list, then into result
    # Iterate over the phrases
    for element in phrases_no_stopword:
        list_of_word_id = []
        # Iterate over the word in the phrase
        for word in element:
            word_id = cursor.execute("""
                        SELECT word_id FROM word_id_word WHERE word = ? 
                    """, word).fetchone()
            list_of_word_id.append(word_id if word_id is not None else -1)

        result.append(list_of_word_id)

    return result

