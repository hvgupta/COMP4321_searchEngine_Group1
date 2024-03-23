import sqlite3

def insert(db:sqlite3.Connection, wordDict:dict[str,int]) -> None:
    if len(wordDict) == 0:
        return
    
    # add the part in which the words which are not in the database are mentioned (with their ID)
    
    arguements:str = ", ".join(wordDict.keys())
    values:str = ", ".join(wordDict.values())
    
    db.execute(f"INSERT INTO wordCount {arguements} VALUES {values}")
    db.commit()