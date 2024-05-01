# This project has been created by Group 1 for the course COMP 4321 (24S)

## Project Phase 1: User manual

The project is based on Python, version ***3.11.0***. The project uses the following packages:

- urllib.parse for handling URLs
- zlib for providing crc32 function which is used to generate page_id
- bs4 for parsing HTML files that are being crawled
- requests to get the content of URLs
- sqlite3 as the dbms (database management system)
- email.utils and datetime to convert RFC 2822 time into timestamp and from timestamp to normal date
- re for regex, to remove the symbols and numbers in the documents
- asyncio, for increasing the running speed
- pathlib to get the absolute path of the files so that the database file can be accessed correctly
- signal and contextmanager, for measuring the running time of web crawling page.
- nltk.stem as stemmer
- itertools, for converting list of 1-tuple to a list
- collections, for the occurrence of the texts
- time, for measuring the overall running time of the program
- argparse, for accepting flags for main.py

Users are required to execute the command on a **_Linux-based_** operating system, with bash or zsh as the shell.

To run the test program, users should do the following. 

1. Users need to ensure they have installed the correct python version. Direct to the directory 

2. Create a virtual environment using the following command. 

    ```bash
    python -m venv .venv
    ```

3. Activate the virtual environment using the following command.

    ```bash
    source .venv/bin/activate
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
   
   Simply go to the webpage mentioned, and you can see the search engine there. 