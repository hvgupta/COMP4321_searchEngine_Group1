from nltk.stem import PorterStemmer as Stemmer
import sqlite3
from zlib import crc32
from pathlib import Path
from itertools import chain
from collections import Counter
import numpy as np

ps = Stemmer()

db_path = str(Path.cwd()) + '/src/files/database.db'

stopword = str(Path.cwd()) + '/src/files/stopwords.txt'

with open(stopword, 'r') as file:
    stopwords = file.read().split()

# Initialize the database
connection = sqlite3.connect(db_path)
cursor = connection.cursor()

def stemWords(words: list) -> list:
    return [ps.stem(word) for word in words]


def removeStopWords(words: list[str]) -> list[str]:
    return [word for word in words if word not in stopwords]


def populate_pageRank(scores: list[int], allPages: list[int]) -> None:
    cursor.execute("DELETE FROM page_rank")
    data: list[tuple[int, float]] = [(allPages[i], scores[i]) for i in range(len(allPages))]
    cursor.executemany("INSERT INTO page_rank(page_id,score) VALUES(?,?)", data)
    connection.commit()


def generateAdjacencyMatrix(allPages: list[int]) -> np.ndarray[np.ndarray[float]]:
    matrixMap: dict[dict[int, float]] = {key: {val: 0 for val in allPages} for key in allPages}

    for page in allPages:
        children: list[int] = cursor.execute("SELECT child_id FROM relation WHERE parent_id = ?", (page,)).fetchall()
        for child in children:
            matrixMap[page][child[0]] = 1

    matrixList: list[list[float]] = [[val for val in matrixMap[key].values()] for key in matrixMap.keys()]
    return np.array(matrixList)


# this code was written by the author of this article: https://medium.com/@TadashiHomer/understanding-and-implementing-the-pagerank-algorithm-in-python-2ce8683f17a3
def page_rank(curPageRankScore: np.ndarray[int], adjacency_matrix: np.ndarray[np.ndarray[int]],
              teleportation_probability: float, max_iterations: int = 100) -> np.ndarray[int]:
    # Initialize the PageRank scores with a uniform distribution
    page_rank_scores = curPageRankScore

    # Iteratively update the PageRank scores
    for _ in range(max_iterations):
        # Perform the matrix-vector multiplication
        new_page_rank_scores = adjacency_matrix.dot(page_rank_scores)

        # Add the teleportation probability
        new_page_rank_scores = teleportation_probability + (1 - teleportation_probability) * new_page_rank_scores
        # Check for convergence
        if np.allclose(page_rank_scores, new_page_rank_scores):
            break

    page_rank_scores = new_page_rank_scores
    return page_rank_scores


def startPageRank() -> None:
    allPages: list[int] = [page[0] for page in cursor.execute("SELECT page_id FROM id_url").fetchall()]
    adjacencyMatrix: np.ndarray[np.ndarray[float]] = generateAdjacencyMatrix(allPages)
    pageRankScores: np.ndarray[float] = page_rank(np.ones(len(allPages)), adjacencyMatrix, 0.85)
    populate_pageRank(pageRankScores, allPages)


def indexer():

    # Get the list of all the pages
    page_ids = cursor.execute("SELECT page_id FROM page_info").fetchall()

    for page_id in page_ids:
        # Get the integer of page_id
        cur_page_id = page_id[0]

        # Fetch all body and title text
        body_text = cursor.execute("SELECT word FROM page_id_word WHERE page_id = ?", (cur_page_id,)).fetchall()
        title_text = cursor.execute("SELECT word FROM title_page_id_word WHERE page_id = ?", (cur_page_id,)).fetchall()

        # Convert them from 1-tuple into lists of words
        body_text = (list(chain.from_iterable(body_text)))
        title_text = (list(chain.from_iterable(title_text)))

        # Remove stopwords, then stem them
        body_text = stemWords(removeStopWords(body_text))
        title_text = stemWords(removeStopWords(title_text))

        # Get a list of all words so that we can put it in word_id_word
        all_words = set(body_text + title_text)

        # Convert them into IDs
        all_words_ids = [int(crc32(str.encode(w))) for w in all_words]

        # Zip them together to put them into database
        word_id_word = list(zip(all_words_ids, all_words))
        page_id_word_stem = (cur_page_id, " ".join(body_text))
        title_id_word_stem = (cur_page_id, " ".join(title_text))

        # # Add index to page_id word
        # for i in range(len(page_id_word_stem)):
        #     page_id_word_stem[i] = (i,) + page_id_word_stem[i]

        # for i in range(len(title_id_word_stem)):
        #     title_id_word_stem[i] = (i,) + title_id_word_stem[i]

        # Put them into database
        cursor.executemany("INSERT INTO word_id_word VALUES (?, ?)", word_id_word)
        cursor.execute("INSERT INTO title_page_id_word_stem VALUES (?, ?)", title_id_word_stem)
        cursor.execute("INSERT INTO page_id_word_stem VALUES (?, ?)", page_id_word_stem)

        # Count the occurrence of the texts
        count_body = list(Counter(body_text).items())
        count_title = list(Counter(title_text).items())

        # Insert the occurrence into the database
        for element in count_body:
            cursor.execute("INSERT INTO inverted_idx VALUES (?,?,?)", (cur_page_id, int(crc32(str.encode(element[0]))), element[1],))

        for element in count_title:
            cursor.execute("INSERT INTO title_inverted_idx VALUES (?,?,?)", (cur_page_id, int(crc32(str.encode(element[0]))), element[1],))

        # Save the changes to database
        connection.commit()

    # Forward Index for body
    lst = cursor.execute("""
        SELECT word_id FROM inverted_idx
    """).fetchall()

    words = list(Counter(list(chain.from_iterable(lst))).items())

    cursor.executemany("""
            INSERT INTO forward_idx VALUES (?,?)
    """, words)

    # Title forward index
    lst = cursor.execute("""
        SELECT word_id FROM title_inverted_idx
    """).fetchall()

    words = list(Counter(list(chain.from_iterable(lst))).items())

    cursor.executemany("""
            INSERT INTO title_forward_idx VALUES (?,?)
    """, words)

    startPageRank()

    connection.commit()

