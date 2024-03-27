import sqlite3
import numpy as np

def insert(db:sqlite3.Cursor, table_name: str, data:np.ndarray) -> None:
    if (type(data) == list):
        data = np.array(data)
    
    if data.size == 0:
        return

    if (data.ndim == 1): # in case if only one value is being supplied
        data = np.expand_dims(data, axis=1)
    
    numArguements:int = data.shape[1]
    
    db.executemany(f"INSERT INTO {table_name} (VALUES (?{",?"*(numArguements-1)})",data)
    db.commit()


def get_column_names(db: sqlite3.Cursor, table_name: str) -> list[str]:
    cursor = db.cursor()
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = [column[1] for column in cursor.fetchall()]
    return columns

def update_value(db: sqlite3.Cursor, table_name: str, documentId:int, wordDict: dict[str,str]) -> None:
    if len(wordDict) == 0:
        return
    
    arguements:str = ", ".join([f"""{key} = {wordDict[key]}""" for key in wordDict.keys()])
    
    db.execute(f"UPDATE {table_name} SET {arguements} WHERE documentId = {documentId}")
    db.commit()