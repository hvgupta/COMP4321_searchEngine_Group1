from nltk.stem import PorterStemmer as Stemmer

ps = Stemmer()

def stemWord(word:str)->str:
    return ps.stem(word)

def stemWords(words:list)->list:
    return [ps.stem(word) for word in words]