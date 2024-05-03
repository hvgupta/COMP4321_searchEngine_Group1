from flask import Flask, render_template, request
import sqlite3

app = Flask(__name__)

@app.route("/")
def searchbar():
    return render_template("index.html")

@app.route("/search/", methods=['POST'])
def submit_search():
    query = request.form['searchbar']
    print(query)

    return render_template("search_results.html")

if __name__ == "__main__":
    app.run(debug=True)