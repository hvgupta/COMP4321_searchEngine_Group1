from nltk.stem import PorterStemmer as Stemmer

ps = Stemmer()

def stemWord(word:str)->str:
    return ps.stem(word)
