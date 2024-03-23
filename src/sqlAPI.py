import sqlite3

def insert(db:sqlite3.Connection, table_name: str, documentId:int ,wordDict:dict[str,int]) -> None:
    if len(wordDict) == 0:
        return
    
    # add the part in which the words which are not in the database are mentioned (with their ID)
    
    arguements:str = ", ".join(wordDict.keys())
    values:str = "','".join(wordDict.values())
    
    
    db.execute(f"INSERT INTO {table_name} (documentId,{arguements}) VALUES ({documentId},{values})")
    db.commit()


def get_column_names(db: sqlite3.Connection, table_name: str) -> list[str]:
    cursor = db.cursor()
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = [column[1] for column in cursor.fetchall()]
    return columns

def update_value(db: sqlite3.Connection, table_name: str, documentId:int, wordDict: dict[str,int]) -> None:
    if len(wordDict) == 0:
        return
    
    arguements:str = ", ".join([f"""{key} = {wordDict[key]}""" for key in wordDict.keys()])
    
    db.execute(f"UPDATE {table_name} SET {arguements} WHERE documentId = {documentId}")
    db.commit()