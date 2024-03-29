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

def tokenize(soup: bsoup,textType:str) -> list[str]:
    if soup is None:
        return []
    return removeStopWords(regex.sub("[^A-Za-z]+", " ", soup.get_text()).split())

def insertInfoInvIdxTable(cursor:sqlite3.Cursor, pageID:int, tableType:str,text:str) -> None:
    stemmedDocument:list[str] = stemWords(text.split())
    
    uniqueWords: np.ndarray[str]
    wordCount: np.ndarray[int]
    uniqueWords, wordCounts = np.unique(stemmedDocument, return_counts=True)
    
    # to check if the page is already in the database
    fetch = cursor.execute(f"SELECT * FROM {tableType}_inverted_idx WHERE page_id=?",(pageID,)).fetchall()
    
    if (len(fetch) != 0):
        delete_from_table(cursor, f"{tableType}_inverted_idx", {"page_id":pageID})
            
    wordCount:np.ndarray[int] = np.expand_dims(wordCounts, axis=1)
    wordID:np.ndarray[int] = np.expand_dims(np.array([crc32(str.encode(word)) for word in uniqueWords]),axis=1)
    pageID:np.ndarray = np.full((uniqueWords.size,1), pageID)
    
    data:np.ndarray = np.hstack((pageID, wordID, wordCount)).tolist()
    insertIntoTable(cursor, f"{tableType}_inverted_idx", data)
    

def insertInfoWordPosTable(cursor:sqlite3.Cursor, pageID:int,text:str, tableType:str = "body") -> None:
    
    uniqueWords: np.ndarray[str] = np.unique(text.split())
    sentenceList: np.ndarray[str] = np.array(text.split())
    
    fetch = cursor.execute(f"SELECT * FROM {tableType}_page_id_word WHERE page_id=?",(pageID,)).fetchall()
    
    if fetch is not None or fetch != []:
        delete_from_table(cursor, f"{tableType}_page_id_word", {"page_id":pageID})
    
    for word in uniqueWords:
        indexes:np.ndarray = np.expand_dims(np.arange(len(sentenceList))[word == np.array(sentenceList)],axis=1)
        pageIds:np.ndarray = np.full((indexes.size,1), pageID)
        wordIds:np.ndarray = np.full((indexes.size,1), crc32(str.encode(word)))
        
        data:list = np.hstack((wordIds,pageIds,indexes)).tolist()
        insertIntoTable(cursor, f"{tableType}_page_id_word", data)
        
def insertInfoWordTable(cursor:sqlite3.Cursor, text:str) -> None:
    uniqueWords: np.ndarray[str] = np.unique(text.split())

    for word in uniqueWords:
        fetch = cursor.execute(f"SELECT * FROM word_id_word WHERE word=?",(word,)).fetchall()
        if fetch is None or fetch == []:    
            insertIntoTable(cursor, "word_id_word", [crc32(str.encode(word)), word])