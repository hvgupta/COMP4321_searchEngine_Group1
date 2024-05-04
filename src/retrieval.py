from urllib.parse import urljoin, urlparse
from zlib import crc32
import requests
import sqlite3
from email.utils import parsedate_to_datetime
from datetime import datetime
import re
import asyncio
from pathlib import Path
from math import log2
from nltk.stem import PorterStemmer as Stemmer
import sqlite3
from itertools import chain
from collections import Counter


# To Harsh:
# The imports on the above are just for reference because they are copied from crawler.py
# Free to add more lib.
# Unless necessary, you are suggested not to add numpy as it may fuck up the project 😔
# Add oil OwO QwQ

ALPHA:int = 0.6 # how important is titles matching
BETA:int = 1 - ALPHA # how important is text matching 
MAX_RESULTS:int = 50

# Create a list of stopwords
stopword = str(Path.cwd()) + '/src/files/stopwords.txt'

# Load database, then create a cursor.
path_of_db = str(Path.cwd()) + '/src/files/database.db'
connection = sqlite3.connect(path_of_db)
cursor = connection.cursor()

# Stemmer
ps = Stemmer()

# Open stopword
with open(stopword, 'r') as file:
    stopwords = file.read().split()


def parse_string(query: str)->list[list[int]]:
    """
    `Input`: query: str: The string entered in the text box
    `Return`: Array of arrays, 
        `index 0`: is the encoding of the all words in the string
        `index 1`: is the encoding of the words which are phrases
    """

    # Create two arrays of phrases and words to be queried.
    phrases = [x.lower() for x in re.findall('"([^"]*)"', query) if x]
    # single_word = [x.lower() for x in re.findall(r'''"[^"]*"|'[^']*'|\b([^\d\W]+)\b''', query) if x]
    single_word = []
    for word in query.split():
        single_word.append(re.sub("[^a-zA-Z-]+", "", word.lower()))

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
    phrase = []
    for element in single_word_no_stopword:
        try: # ignore the word if it is not in the database
            word_id = cursor.execute("""
                SELECT word_id FROM word_id_word WHERE word = ? 
            """, (element,)).fetchone()[0]
            phrase.append(word_id)
        except:
            pass
    result.append(phrase)

    phraseList = []
    # Put the converted phrase into a list, then into result
    # Iterate over the phrases
    for element in phrases_no_stopword:
        list_of_word_id = []
        words = element.split()
        # Iterate over the word in the phrase
        for word in words:
            try: # ignore the word if it is not in the database
                word_id = cursor.execute("""
                            SELECT word_id FROM word_id_word WHERE word = ? 
                        """, (word,)).fetchone()[0]
                list_of_word_id.append(word_id)
            except:
                pass

        phraseList.append(list_of_word_id)
    result.append(phraseList)
    
    return result

def documentToVec(page_id:int,fromTitle:bool=False)->dict[int,int]:
    table:str = "inverted_idx"
    vector:dict[int,int] = {}
    if fromTitle:
        table = "title_inverted_idx"
        
    wordList:list[list[int]] = cursor.execute(
        f"""
            SELECT word_id, count FROM {table} WHERE page_id = ?
        """, (page_id,)).fetchall() 
        
    maxTF:int = cursor.execute(
        f"""
            SELECT MAX(count) FROM {table} WHERE page_id = ?                   
        """, (page_id,)).fetchone()[0]
    
    documentCount:int = cursor.execute(
        f"""
            SELECT COUNT(DISTINCT page_id) FROM {table}
        """).fetchone()[0]
    
    for word,tf in wordList:
        countOfDocument:int = cursor.execute(
            f"""
                SELECT COUNT(DISTINCT page_id) FROM {table} WHERE word_id = ?
            """,(word,)).fetchone()[0]
        
        vector[word] = tf * log2(float(documentCount)/countOfDocument) / float(maxTF)
    
    return vector   

def queryToVec(queryEncoding:list[int],table:str)->dict[int,int]:
    
    vector:dict[int,int] = {}
    
    wordsTF:dict[int,int] = Counter(queryEncoding)
    maxTF: int = max(wordsTF.values())

    documentCount:int = cursor.execute(
        f"""
            SELECT COUNT(DISTINCT page_id) FROM {table}
        """).fetchone()[0]
    
    for word,tf in list(wordsTF.items()):
        countOfDocument:int = cursor.execute(
            """
                SELECT COUNT(DISTINCT page_id) FROM word_id_word WHERE word_id = ?
            """,(word,)).fetchone()[0]
        
        vector[word] = tf * log2(documentCount/countOfDocument) / float(maxTF)
    
    return vector


def cosineSimilarity(queryVector:dict[int,int],documentVector:dict[int,int])->float:
    """
        Input: takes two dictionaries, both of them have the `word_id` as the key and the corresponding tfxidf/max(tf) as the value
        output: it is a relative output of cosine distance.
                Magnitude of the query vector is not calculated since it is constant 
    """
    
    reduced_queryVector = {key: value for key, value in queryVector.items() if key in documentVector}
    reduced_documentVector = {key: value for key, value in documentVector.items() if key in queryVector}
    
    dotProduct:float = sum(reduced_queryVector[word] * reduced_documentVector[word] for word in reduced_queryVector)
    documentMagnitude:float = sum(value**2 for value in documentVector.values()) ** 0.5
    
    return dotProduct / documentMagnitude

def search_engine(query: str):
    
    splitted_query:list[list[int]] = parse_string(query)
    queryVector_title:dict[int,int] = queryToVec(splitted_query[0],"title_inverted_idx")
    queryVector_text:dict[int,int] = queryToVec(splitted_query[0],"inverted_idx")
    
    allDocuments:list[int] = cursor.execute(
        """
            SELECT DISTINCT(page_id) FROM id_url
        """
        ).fetchall()
    
    title_cosineScores:dict[int,float] = {}
    text_cosineScores:dict[int,float] = {}
    for document in allDocuments:
        
        title_documentVector:dict[int,int] = documentToVec(document,True)
        text_documentVector:dict[int,int] = documentToVec(document)
        
        title_similarity:float = cosineSimilarity(queryVector_title,title_documentVector)
        text_similarity:float = cosineSimilarity(queryVector_text,text_documentVector)
        
        title_cosineScores[document] = title_similarity
        text_cosineScores[document] = text_similarity
        
    title_cosineScores = dict(sorted(title_cosineScores.items(), key=lambda item: item[1],reverse=True)[:MAX_RESULTS])
    text_cosineScores = dict(sorted(text_cosineScores.items(), key=lambda item: item[1],reverse=True)[:MAX_RESULTS])
    
    combined_cosineScores:dict[int,float] = {}
    for (title_key,title_val),(text_key,text_val) in zip(title_cosineScores.items(),text_cosineScores.items()):
        if title_key in combined_cosineScores:
            combined_cosineScores[title_key] += ALPHA * title_val
        else:
            combined_cosineScores[title_key] = ALPHA * title_val
        
        if text_key in combined_cosineScores:
            combined_cosineScores[text_key] += BETA * text_val
        else:
            combined_cosineScores[text_key] = BETA * text_val
    
    
    return combined_cosineScores