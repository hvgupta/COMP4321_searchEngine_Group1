import sqlite3
import numpy as np

def insertIntoTable(db:sqlite3.Cursor, table_name: str, data:np.ndarray) -> None:
    if (type(data) == list):
        data = np.array(data)
    
    if data.size == 0:
        return

    if (data.ndim == 1): # in case if only one value is being supplied
        data = np.expand_dims(data, axis=0)
    
    numArguements:int = data.shape[1]
    
    placeholders = ', '.join('?' * numArguements)
    db.executemany(f"INSERT INTO {table_name} VALUES ({placeholders})", data.tolist())


def get_column_names(db: sqlite3.Cursor, table_name: str) -> list[str]:
    cursor = db.cursor()
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = [column[1] for column in cursor.fetchall()]
    return columns

def update_value(db: sqlite3.Cursor, table_name: str, updateDict:dict[str,str], conditions: dict[str,str]) -> None:
    if len(conditions) == 0:
        return
    
    cond:str = ",".join([f"{key} = '{value}'" for key, value in conditions.items()])
    values:str = ",".join([f"{key} = '{value}'" for key, value in updateDict.items()])
    
    db.execute(f"UPDATE {table_name} SET {values} WHERE {cond}")