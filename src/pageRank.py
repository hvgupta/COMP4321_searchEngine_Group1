import sqlite3
import numpy as np
from pathlib import Path

path_of_db = str(Path.cwd()) + '/src/files/database.db'
connection = sqlite3.connect(path_of_db, check_same_thread=False)  # Set check_same_thread to False because Flask initialized the connection in a different thread, this is safe because the search engine is read only
cursor = connection.cursor()

def populate_pageRank(scores:list[int],allPages:list[int])->None:
    try:
        cursor.execute("DELETE FROM page_rank")
    except:
        pass
    data:list[tuple[int,float]] = [(allPages[i],scores[i]) for i in range(len(allPages))]
    cursor.executemany("INSERT INTO page_rank(page_id,score) VALUES(?,?)",data)
    connection.commit()

def generateAdjacencyMatrix(allPages:list[int])->np.ndarray[np.ndarray[float]]:
    matrixMap:dict[dict[int,float]] = {startNode:{endNode:0 for endNode in allPages} for startNode in allPages}
    
    for page in allPages:
        children:list[int] =  cursor.execute("SELECT child_id FROM relation WHERE parent_id = ?", (page,)).fetchall()
        for child in children:
            matrixMap[page][child[0]] = 1
            
    matrixList:list[list[float]] = [[val for val in matrixMap[key].values()] for key in matrixMap.keys()]
    return np.array(matrixList)    

# this code was written by the author of this article: https://medium.com/@TadashiHomer/understanding-and-implementing-the-pagerank-algorithm-in-python-2ce8683f17a3
def page_rank(curPageRankScore:np.ndarray[int],adjacency_matrix:np.ndarray[np.ndarray[int]],
              teleportation_probability:float, max_iterations:int=100)->np.ndarray[int]:
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

def startPageRank()->None:
    allPages:list[int] = [page[0] for page in cursor.execute("SELECT DISTINCT page_id FROM id_url").fetchall()]
    adjacencyMatrix:np.ndarray[np.ndarray[float]] = generateAdjacencyMatrix(allPages)
    pageRankScores:np.ndarray[float] = page_rank(np.ones(len(allPages)),adjacencyMatrix, 0.85)
    populate_pageRank(pageRankScores,allPages)
    
# startPageRank()