from nltk.stem import PorterStemmer as Stemmer
import re
from bs4 import BeautifulSoup as bsoup
from src.sqlAPI import *
import numpy as np
import pathlib
from zlib import crc32
import regex

ps = Stemmer()

with open(pathlib.Path(__file__).parent/'files/stopwords.txt', 'r') as file:
    stopwords = file.read().split()

def stemWords(words: list) -> list:
    return [ps.stem(word) for word in words]

def removeStopWords(words: list[str]) -> list[str]:
    wrdList: np.ndarray[str] = np.array(words)
    stpwords: np.ndarray[str] = np.array(stopwords)
    return wrdList[~np.isin(wrdList, stpwords)].tolist()

def tokenize(soup: bsoup) -> list[str]:
    if soup is None:
        return []
    return removeStopWords(regex.sub(' ', soup.find("body").text).split())

def updateInvertedIndex(cursor:sqlite3.Cursor ,document:bsoup, pageID:int) -> None:
    stemmedDocument:list[str] = stemWords(tokenize(document))
    
    uniqueWords: np.ndarray[str]
    wordCount: np.ndarray[int]
    uniqueWords, wordCounts = np.unique(stemmedDocument, return_counts=True)
    
    # to check if the page is already in the database
    fetch = cursor.execute("SELECT * FROM inverted_idx WHERE page_id=?",pageID).fetchall()
    
    if (len(fetch) != 0):
        delete_from_table(cursor, "inverted_idx", {"page_id":pageID})
            
    wordCount:np.ndarray[int] = np.expand_dims(wordCounts, axis=1)
    wordID:np.ndarray[int] = np.expand_dims(np.array([crc32(str.encode(word)) for word in uniqueWords]),axis=1)
    pageID:np.ndarray = np.full((uniqueWords.size,1), pageID)
    
    data:np.ndarray = np.hstack((pageID, wordID, wordCount)).tolist()
    insertIntoTable(cursor, "inverted_idx", data)
    
def updateTitleInvertedIndex(cursor:sqlite3.Cursor ,document:bsoup, pageID:int) -> None:
    stemmedDocument:list[str] = stemWords(removeStopWords(regex.sub(' ', document.find("title").text).split()))
    
    uniqueWords: np.ndarray[str]
    wordCount: np.ndarray[int]
    uniqueWords, wordCounts = np.unique(stemmedDocument, return_counts=True)
    
    # to check if the page is already in the database
    fetch = cursor.execute("SELECT * FROM title_inverted_idx WHERE page_id=?",pageID).fetchall()
    
    if (len(fetch) != 0):
        delete_from_table(cursor, "title_inverted_idx", {"page_id":pageID})
            
    wordCount:np.ndarray[int] = np.expand_dims(wordCounts, axis=1)
    wordID:np.ndarray[int] = np.expand_dims(np.array([crc32(str.encode(word)) for word in uniqueWords]),axis=1)
    pageID:np.ndarray = np.full((uniqueWords.size,1), pageID)
    
    data:np.ndarray = np.hstack((pageID, wordID, wordCount)).tolist()
    insertIntoTable(cursor, "title_inverted_idx", data)
    