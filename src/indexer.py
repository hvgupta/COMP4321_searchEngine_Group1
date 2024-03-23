from nltk.stem import PorterStemmer as Stemmer
import re
from bs4 import BeautifulSoup as bsoup
import crawler
from sqlAPI import *
import numpy as np
import pathlib

# Remove all punctuations that are not letters.
regex = re.compile('[^a-zA-Z]')

ps = Stemmer()

db = sqlite3.connect(pathlib.Path(__file__).parent/"files/wordCount.db")

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

def inverseIndexCreator(document:bsoup) -> None:
    stemmedDocument:list[str] = stemWords(tokenize(document))
    
    uniqueWords: np.ndarray[str]
    wordCount: np.ndarray[int]
    uniqueWords, wordCount = np.unique(stemmedDocument, return_counts=True)
    
    wordDict: dict[str, int] = dict(zip(uniqueWords, wordCount))
    insert(db, wordDict)
    
