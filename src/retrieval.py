import sqlite3
import re
from pathlib import Path
from math import log2
from nltk.stem import PorterStemmer as Stemmer
import sqlite3
from itertools import chain
from collections import Counter
from time import time


# To Harsh:
# The imports on the above are just for reference because they are copied from crawler.py
# Free to add more lib.
# Unless necessary, you are suggested not to add numpy as it may fuck up the project 😔
# Add oil OwO QwQ

ALPHA:float = 0.6 # how important is titles matching
BETA:float = 1 - ALPHA # how important is text matching 
MAX_RESULTS:int = 50 # max results that can be returned

# Create a list of stopwords
stopword = str(Path.cwd()) + '/src/files/stopwords.txt'

# Load database, then create a cursor.
path_of_db = str(Path.cwd()) + '/src/files/database.db'
connection = sqlite3.connect(path_of_db, check_same_thread=False)  # Set check_same_thread to False because Flask initialized the connection in a different thread, this is safe because the search engine is read only
cursor = connection.cursor()

DOCUMENT_COUNT:int = cursor.execute("""
    SELECT COUNT(page_id) from id_url
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
        result = r"(?<!\S){}(?!\S)".format(" ".join(resultwords))

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

    result.append(phrases_no_stopword)
    
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

def queryToVec(queryEncoding:list[int],table:str)->dict[int,int]:
    
    if (len(queryEncoding) == 0):
        return {}
    
    vector:dict[int,int] = {}
    
    wordsTF:dict[int,int] = Counter(queryEncoding)
    maxTF: int = max(wordsTF.values())
    
    for word,tf in list(wordsTF.items()):
        countOfDocument:int = cursor.execute(
            f"""
                SELECT COUNT(DISTINCT page_id) FROM {table} WHERE word_id = ?
            """,(word,)).fetchone()[0] + 1
        
        vector[word] = tf * log2(float(DOCUMENT_COUNT)/countOfDocument) / float(maxTF)
    
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

    documentTitle_list:list[set[str]] = cursor.execute(
        """
            SELECT word FROM title_page_id_word_stem WHERE page_id = ?
        """, 
        (document_id,)).fetchall()
    documentTitle:str = " ".join(list(chain.from_iterable(documentTitle_list)))
    
    documentText_List:list[set[str]] = cursor.execute(
        """
            SELECT word FROM page_id_word_stem WHERE page_id = ?
        """, 
        (document_id,)).fetchall()
    documentText:str = " ".join(list(chain.from_iterable(documentText_List)))

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

    documentTitle_list:list[int] = cursor.execute(
        """
            SELECT word_id FROM title_inverted_idx WHERE page_id = ?
        """, 
        (document_id,)).fetchall()
    documentTitle:list[int] = [x[0] for x in documentTitle_list]
    
    documentText_List:list[int] = cursor.execute(
        """
            SELECT word_id FROM inverted_idx WHERE page_id = ?
        """, 
        (document_id,)).fetchall()
    documentText:list[int] = [x[0] for x in documentText_List]

    for word in query:
        if word in documentTitle or word in documentText:
            return True

    return False

def search_engine(query: str)->dict[int,float]:

    splitted_query:list[list[int]] = parse_string(query)
    if (len(splitted_query[0]) == 0): # incase query is something out of the db
        return {}
    
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
        document = document[0]
        if (len(splitted_query[1]) > 0):
            if not phraseFilter(document,splitted_query[1]):
                continue
        else:
            if not queryFilter(document,splitted_query[0]):
                continue            
        
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
    combined_cosineScores = dict(sorted(combined_cosineScores.items(), key=lambda item: item[1],reverse=True)[:MAX_RESULTS])

    return combined_cosineScores

# start = time()
# results = search_engine('hong kong university of science and technology')
# end = time()
# print("Time taken: ", end - start)
# print(results)