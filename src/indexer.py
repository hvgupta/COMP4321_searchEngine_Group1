from nltk.stem import PorterStemmer as Stemmer
import re
from bs4 import BeautifulSoup as bsoup
import crawler

# Remove all punctuations that are not letters.
regex = re.compile('[^a-zA-Z]')

ps = Stemmer()

with open('files/stopwords.txt', 'r') as file:
    stopwords = file.read().split()


def removeStopWords(words: list) -> list:
    return [word for word in words if word not in stopwords]


def tokenize(soup: bsoup) -> list:
    if soup is None:
        return []
    return removeStopWords(regex.sub('', soup.find("body").text).split())


def stemWords(words: list) -> list:
    return [ps.stem(word) for word in words]


