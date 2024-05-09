from flask import Flask, render_template, make_response, request
import sqlite3
import timeit
from typing import List
import json

from src import retrieval
from src.util import SearchResult

app = Flask(__name__)

@app.route("/")
def searchbar():
    """
    Displays the homepage and search bar of the search engine.
    """

    # Get search history
    history = json.loads(request.cookies.get('history', default="{}"))

    return render_template("index.html")

@app.route("/search/", methods=['POST'])
def submit_search():
    """
    Performs the search and displays the results in the webpage.
    """

    # Get query from search bar
    query: str = request.form['searchbar']

    # Time the search operation
    start_time: float = timeit.default_timer()
    # Pass query into search engine
    # query_parsed: list = retrieval.parse_string(query)
    # search_results_raw: dict = retrieval.search_engine(query_parsed)
    # search_results_raw: dict = retrieval.search_engine([])  # DEBUG SKIP
    search_results_raw: dict = retrieval.search_engine(query)
    search_time_taken: float = timeit.default_timer() - start_time

    # Get data of the search results
    # k: page ID
    # v: page score
    search_results: list[SearchResult] = []
    for k, v in sorted(search_results_raw.items(), key=lambda x: x[1], reverse=True):  # Sort the search results by score
        if v != 0:
            search_results.append(SearchResult(k, v))

    # Set up response
    resp = make_response(
        render_template(
            "search_results.html",
            QUERY=query,
            RESULTS=search_results,
            TIME_TAKEN=search_time_taken
        )
    )

    # Add query to search history
    history: List[str] = json.loads(request.cookies.get('history', default="{}"))
    history.append(query)
    resp.set_cookie("history", json.dumps(history))

    return resp

if __name__ == "__main__": 
    app.run(debug=True)