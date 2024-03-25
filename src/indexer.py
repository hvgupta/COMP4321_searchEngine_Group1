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

def inverseIndexCreator(cursor:sqlite3.Cursor ,document:bsoup, documentID:int) -> None:
    stemmedDocument:list[str] = stemWords(tokenize(document))
    
    uniqueWords: np.ndarray[str]
    wordCount: np.ndarray[int]
    uniqueWords, wordCount = np.unique(stemmedDocument, return_counts=True)
    
    currentVocab: np.ndarray[str] = np.array(get_column_names(cursor, "wordCount"))
    truthTable: np.ndarray[bool] = np.isin(uniqueWords, currentVocab)
    
    notInVocab: np.ndarray[str] = uniqueWords[~truthTable]
    notInVocabCount: np.ndarray[int] = wordCount[~truthTable]
    outWordDict: dict[str, int] = dict(zip(notInVocab, notInVocabCount))
    
    inVocab: np.ndarray[str] = uniqueWords[truthTable]
    inVocabCount: np.ndarray[int] = wordCount[truthTable]
    wordDict: dict[str, int] = dict(zip(inVocab, inVocabCount))

    insert(cursor, "wordCount", documentID,wordDict)
    
    
    
    
    
