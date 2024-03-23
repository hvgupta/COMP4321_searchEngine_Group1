from nltk.stem import PorterStemmer as Stemmer
import re
from bs4 import BeautifulSoup as bsoup
import sqlite3
import numpy as np
from zlib import crc32

# Remove all punctuations that are not letters.
regex = re.compile('[^a-zA-Z]')

ps = Stemmer()

db = sqlite3.connect('files/database.db')

with open('files/stopwords.txt', 'r') as file:
    stopwords = file.read().split()


def stemWords(words: list) -> list:
    return [ps.stem(word) for word in words]


def removeStopWords(words: np.ndarray[str]) -> np.ndarray[str]:
    wrdList: np.ndarray[str] = np.array(words)
    stpwords: np.ndarray[str] = np.array(stopwords)
    return wrdList[~np.isin(wrdList, stpwords)]


def tokenize(soup: bsoup) -> list[str]:
    if soup is None:
        return []
    return removeStopWords(regex.sub(' ', soup.find("body").text).split())


def inverseIndexCreator(document: bsoup) -> None:
    stemmedDocument: list[str] = stemWords(tokenize(bsoup))


def invertedIndexFromPages(title=False):
    # Mode selection
    target_table = {False: "page_id_word", True: "title_page_id_word"}
    target_inv_idx = {False: "inverted_idx", True: "title_inverted_idx"}

    con = sqlite3.connect("files/database.db")
    cur = con.cursor()

    # Fetch list of all pages
    res_pages = cur.execute(f"SELECT DISTINCT page_id FROM {target_table[title]}")
    pages = res_pages.fetchall()

    for page_id in pages:
        # Get list of words in a page
        page_id_unpacked = page_id[0]  # fetchall() puts each row in a tuple
        res_words_in_page = cur.execute(f"SELECT word FROM {target_table[title]} WHERE page_id = ?", page_id)
        words_in_page = np.array(res_words_in_page.fetchall()).flatten()

        # Count the occurrence of each word
        word, freq = np.unique(words_in_page, return_counts=True)
        word_ids = [crc32(str.encode(w)) for w in word]  # Encode words into their ID
        page_ids = np.full_like(word, fill_value=page_id)

        # Add each row to the table
        new_rows = np.transpose([page_ids, word_ids, freq])
        cur.executemany(f"INSERT INTO {target_inv_idx[title]} VALUES(?, ?, ?)", new_rows)
        con.commit()