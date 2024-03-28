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

def updateInvertedIndex(cursor:sqlite3.Cursor ,document:bsoup, documentID:int) -> None:
    stemmedDocument:list[str] = stemWords(tokenize(document))
    
    uniqueWords: np.ndarray[str]
    wordCount: np.ndarray[int]
    uniqueWords, wordCounts = np.unique(stemmedDocument, return_counts=True)

    wordCount:np.ndarray[int] = np.expand_dims(wordCounts, axis=1)
    wordID:np.ndarray[int] = np.expand_dims(np.array([crc32(str.encode(word)) for word in uniqueWords]),axis=1)
    documentID:np.ndarray = np.full((uniqueWords.size,1), documentID)
    
    data:np.ndarray = np.hstack((documentID, wordID, wordCount)).tolist()
    
    insert(cursor, "inverted_idx", data)