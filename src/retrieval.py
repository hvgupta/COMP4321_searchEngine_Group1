import sqlite3
import re
from pathlib import Path
from math import log2
from nltk.stem import PorterStemmer as Stemmer
import sqlite3
from collections import Counter
from time import time
import numpy as np


# To Harsh:
# The imports on the above are just for reference because they are copied from crawler.py
# Free to add more lib.
# Unless necessary, you are suggested not to add numpy as it may fuck up the project 😔
# Add oil OwO QwQ

ALPHA:float = 0.75 # how important is titles matching
BETA:float = 1 - ALPHA # how important is text matching 
MAX_RESULTS:int = 50 # max results that can be returned

Title_globalPageDict:dict[int,dict[int,int]] = {}
Text_globalPageDict:dict[int,dict[int,int]] = {}

globalWordtoID:dict[str,int] = {}

Title_globalPageStemText:dict[int,str] = {}
Text_globalPageStemText:dict[int,str] = {}

allDocs:list[int] = []

# Create a list of stopwords
stopword = str(Path.cwd()) + '/src/files/stopwords.txt'

# Load database, then create a cursor.
path_of_db = str(Path.cwd()) + '/src/files/database.db'
connection = sqlite3.connect(path_of_db, check_same_thread=False)  # Set check_same_thread to False because Flask initialized the connection in a different thread, this is safe because the search engine is read only
cursor = connection.cursor()

DOCUMENT_COUNT:int = cursor.execute(
    """
        SELECT COUNT(page_id) FROM id_url
    """).fetchone()[0]

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
    resultArray = []
    # Create two arrays of phrases and words to be queried.
    # single_word = [x.lower() for x in re.findall(r'''"[^"]*"|'[^']*'|\b([^\d\W]+)\b''', query) if x]
    start = time()
    single_word = []
    for idx,word in enumerate(query.split()):
        if (idx == 10000):
            break
        processedWord:str = re.sub("[^a-zA-Z-]+", "", word.lower())
        stemmedWord:str
        if (processedWord not in stopwords):
            stemmedWord = ps.stem(processedWord)
            try:
                single_word.append(globalWordtoID[stemmedWord])
            except:
                pass
    resultArray.append(single_word)
    end = time()
    print("time taken for query:", end - start)
    
    # Remove every stopwords in the single_word as they are not necessary.
    # During the process we will also stem the word
    # single_word_no_stopword = [ps.stem(x) for x in single_word if x not in stopwords]
    phrases_no_stopword = []
    phrases = [x.lower() for x in re.findall('"([^"]*)"', query) if x]
    for phrase in phrases:
        querywords = phrase.split()

        resultwords = [ps.stem(word) for word in querywords if word.lower() not in stopwords]
        result = r"(?<!\S){}(?!\S)".format(" ".join(resultwords))

        phrases_no_stopword.append(result)

    resultArray.append(phrases_no_stopword)
    
    return resultArray

def documentToVec(page_id:int,fromTitle:bool=False)->dict[int,int]:
    table:str = "inverted_idx"
    vector:dict[int,int] = {}
    
    if page_id == None:
        return vector
    
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
    
    forwardIdx:str = "forward_idx"
    if fromTitle:
        forwardIdx = "title_forward_idx"
        
    word_ids:list[int] = []
    queryArray:list[str] = []
    for word,_ in wordList:
        word_ids.append(word)
        queryArray.append("?")
        
    
    word_counts = cursor.execute(
        f"""
            SELECT word_id, count FROM {forwardIdx} WHERE word_id IN ({','.join(queryArray)})
        """, word_ids).fetchall()
    
    countOfDocument = {word_id: count for word_id, count in word_counts}
    
    for word, tf in wordList:
        
        vector[word] = tf * log2(float(DOCUMENT_COUNT) / countOfDocument[word]) / maxTF
    
    return vector   

def queryToVec(queryEncoding:list[int])->dict[int,int]:
    
    if (len(queryEncoding) == 0):
        return {}
    
    vector:dict[int,int] = {}
    
    wordsTF:dict[int,int] = Counter(queryEncoding)
    
    for word,tf in list(wordsTF.items()):
        vector[word] = tf
    
    return vector

def cosineSimilarity(queryVector:dict[int,int],documentVector:dict[int,int])->float:
    """
        Input: takes two dictionaries, both of them have the `word_id` as the key and the corresponding tfxidf/max(tf) as the value
        output: it is a relative output of cosine distance.
                Magnitude of the query vector is not calculated since it is constant 
    """
    
    if (len(queryVector) == 0 or len(documentVector) == 0):
        return 0.0
    
    reduced_queryVector = {key: value for key, value in queryVector.items() if key in documentVector}
    reduced_documentVector = {key: value for key, value in documentVector.items() if key in queryVector}
    
    dotProduct:float = sum(reduced_queryVector[word] * reduced_documentVector[word] for word in reduced_queryVector)
    documentMagnitude:float = sum(value**2 for value in documentVector.values()) ** 0.5
    
    return dotProduct / documentMagnitude

def phraseFilter(document_id:int, phases:list[str]) -> bool:
    """
    `Input`: document_id: int: The id of the document
    `Input`: phases: list[list[int]]: The list of phrases to be queried
    `Return`: bool: True if the document contains all the phrases, False otherwise
    """
    if (len(phases) == 0 or len(phases[0]) == 0):
        return True

    documentTitle:str = Title_globalPageStemText[document_id]
    
    documentText:list[set[str]] = Text_globalPageStemText[document_id]

    for phrase in phases:
        if not re.search(phrase, documentTitle) and not re.search(phrase, documentText):
            return False    

    return True

def queryFilter(document_id:int, query:list[int]) -> bool:
    """
    `Input`: document_id: int: The id of the document
    `Input`: query: list[int]: The list of words to be queried
    `Return`: bool: True if the document contains any of the words, False otherwise
    """
    if (len(query) == 0):
        return True

    documentTitle_list:list[int] = list(Title_globalPageDict[document_id].keys())
    
    documentText_List:list[int] = list(Text_globalPageDict[document_id].keys())

    for word in query:
        if word in documentTitle_list or word in documentText_List:
            return True

    return False

def search_engine(query: str)->dict[int,float]:
    if (query == None or query == ""):
        return {}
    
    splitted_query:list[list[int]] = parse_string(query)
    if (len(splitted_query[0]) == 0): # incase query is something out of the db
        return {}
    
    queryVector:dict[int,int] = queryToVec(splitted_query[0])

    
    title_cosineScores:dict[int,float] = {}
    text_cosineScores:dict[int,float] = {}

    for document in allDocs:
        document = document[0]
        if (len(splitted_query[1]) > 0):
            if not phraseFilter(document,splitted_query[1]):
                continue
        else:
            if not queryFilter(document,splitted_query[0]):
                continue            
        
        title_documentVector:dict[int,int] = Title_globalPageDict[document]
        text_documentVector:dict[int,int] = Text_globalPageDict[document]
        
        title_similarity:float = cosineSimilarity(queryVector,title_documentVector)
        text_similarity:float = cosineSimilarity(queryVector,text_documentVector)
        
        title_cosineScores[document] = title_similarity
        text_cosineScores[document] = text_similarity
    
    title_cosineScores = dict(sorted(title_cosineScores.items(), key=lambda item: item[1],reverse=True)[:MAX_RESULTS])
    text_cosineScores = dict(sorted(text_cosineScores.items(), key=lambda item: item[1],reverse=True)[:MAX_RESULTS])

    combined_Scores:dict[int,float] = {}
    for (title_key,title_val),(text_key,text_val) in zip(title_cosineScores.items(),text_cosineScores.items()):
        if title_key in combined_Scores:
            combined_Scores[title_key] += ALPHA * title_val
        else:
            combined_Scores[title_key] = ALPHA * title_val
        
        if text_key in combined_Scores:
            combined_Scores[text_key] += BETA * text_val
        else:
            combined_Scores[text_key] = BETA * text_val
    
    pageRankScore:list[tuple[int,float]] = cursor.execute(
        f"""
            SELECT page_id, score FROM page_rank
            WHERE page_id IN ({",".join('?' for _ in combined_Scores)})
        """, tuple(combined_Scores.keys())).fetchall()
    combined_Scores = {page_id: score*pageRank for (page_id,score),(_,pageRank) in zip(combined_Scores.items(),pageRankScore)}
    
    combined_Scores = dict(sorted(combined_Scores.items(), key=lambda item: item[1],reverse=True)[:MAX_RESULTS])

    return combined_Scores

allDocs:list[int] = cursor.execute(
    """
        SELECT page_id FROM id_url                              
    """).fetchall()

for doc in allDocs:
    doc = doc[0]
    Title_globalPageDict[doc] = documentToVec(doc,True)
    Text_globalPageDict[doc] = documentToVec(doc)
    
    Title_globalPageStemText[doc] = cursor.execute(
        """
            SELECT word FROM title_page_id_word_stem WHERE page_id = ?
        """,(doc,)).fetchone()[0]
    Text_globalPageStemText[doc] = cursor.execute(
        """
            SELECT word FROM page_id_word_stem WHERE page_id = ?
        """,(doc,)).fetchone()[0]

for word_id,word in cursor.execute(
    """
        SELECT word_id, word FROM word_id_word
    """).fetchall():
    globalWordtoID[word] = word_id


# start = time()
# results = search_engine('"UG"')
# end = time()
# print("time taken: ", end - start)
# print(results)