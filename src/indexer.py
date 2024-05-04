from nltk.stem import PorterStemmer as Stemmer
import sqlite3
from zlib import crc32
from pathlib import Path
from itertools import chain
from collections import Counter

ps = Stemmer()

db_path = str(Path.cwd()) + '/src/files/database.db'

stopword = str(Path.cwd()) + '/src/files/stopwords.txt'

with open(stopword, 'r') as file:
    stopwords = file.read().split()


def stemWords(words: list) -> list:
    return [ps.stem(word) for word in words]


def removeStopWords(words: list[str]) -> list[str]:
    return [word for word in words if word not in stopwords]


def indexer():
    # Initialize the database
    connection = sqlite3.connect(db_path)
    cursor = connection.cursor()

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
        page_id_word_stem = list(zip([cur_page_id] * len(body_text), body_text))
        title_id_word_stem = list(zip([cur_page_id] * len(title_text), title_text))

        # Add index to page_id word
        for i in range(len(page_id_word_stem)):
            page_id_word_stem[i] = (i,) + page_id_word_stem[i]

        for i in range(len(title_id_word_stem)):
            title_id_word_stem[i] = (i,) + title_id_word_stem[i]

        # Put them into database
        cursor.executemany("INSERT INTO word_id_word VALUES (?, ?)", word_id_word)
        cursor.executemany("INSERT INTO title_page_id_word_stem VALUES (?, ?, ?)", title_id_word_stem)
        cursor.executemany("INSERT INTO page_id_word_stem VALUES (?, ?, ?)", page_id_word_stem)

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
