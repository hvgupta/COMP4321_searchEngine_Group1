# COMP 4321 (24S) Group 1 Group Project, by Gupta Harsh Vardhan, Kong Tsz Yui and Zhang Zhe.

## Project User manual

Demo Video: [YouTube](https://www.youtube.com/watch?v=zf9KNITW1DY)

The project is based on Python, version ***3.12.0***. The project uses the following packages:

- urllib.parse for handling URLs
- zlib for providing crc32 function which is used to generate page_id
- bs4 for parsing HTML files that are being crawled
- requests to get the content of URLs
- sqlite3 as the dbms (database management system)
- email.utils and datetime to convert RFC 2822 time into timestamp and from timestamp to normal date
- re for regex, to remove the symbols and numbers in the documents
- asyncio, for increasing the running speed by asynchronous
- pathlib to get the absolute path of the files so that the database file can be accessed correctly
- nltk.stem as stemmer
- itertools, for converting list of 1-tuple to a list
- collections, for counting the occurrence of the texts
- numpy, for calculating the pagerank
- math, for the calculation of idf.
- time, for measuring the overall running time of the program
- flask, for the frontend
- timeit, to count the running time for the query. 

Users are suggested to run the program in macOS or Linux, with bash or zsh as the shell since the coding and tests are performed on a Unix-based platform. However, they can also run the program on Windows.

To run the program, users should do the following. 

1. Users need to ensure they have installed the correct Python version. Navigate to the directory where the code is downloaded to.

2. Create a virtual environment using the following command. 

    ```bash
    python -m venv .venv
    ```

3. Activate the virtual environment using the following command.

    (Unix-based OS)
    ```bash
    source .venv/bin/activate
    ```

    (Windows)
    ```bash
    .\.venv\Scripts\activate
    ```
    
    
4. Install the required package

    ```bash
    pip install -r requirements.txt
    ```

5. Run the program. The program shall do everything, including initializing database.

    ```bash
    python main.py
    ```
   
6. Now you may see a line mentioning something like
   
   ```
   * Running on http://127.0.0.1:5000
   ```
   
   Simply go to the [127.0.0.1:5000](127.0.0.1:5000), and you can see the search engine there. 
