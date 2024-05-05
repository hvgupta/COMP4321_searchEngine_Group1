from flask import Flask, render_template, request
import sqlite3

from typing import List

from src import retrieval
from src.util import SearchResult

app = Flask(__name__)

@app.route("/")
def searchbar():
    return render_template("index.html")

@app.route("/search/", methods=['POST'])
def submit_search():
    """
    Performs the search and displays the results in the webpage.
    """

    # Get query from search bar
    query: str = request.form['searchbar']

    # Pass query into search engine
    # query_parsed: list = retrieval.parse_string(query)
    # search_results_raw: dict = retrieval.search_engine(query_parsed)
    # search_results_raw: dict = retrieval.search_engine([])  # DEBUG SKIP
    search_results_raw: dict = retrieval.search_engine(query)

    # Get data of the search results
    # k: page ID
    # v: page score
    search_results: list[SearchResult] = []
    for k, v in sorted(search_results_raw.items(), key=lambda x: x[1], reverse=True):  # Sort the search results by score
        if v != 0:
            search_results.append(SearchResult(k, v))

    return render_template(
        "search_results.html",
        QUERY=query,
        RESULTS=search_results
    )

if __name__ == "__main__":
    app.run(debug=True)