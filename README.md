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

5. Run the test program to crawl pages into database using the following command. (This is for phase 1 only.)

    The test program consists of two inputs, which are the url of the website to be crawled, and
    the number of pages to be crawled. The usage is shown as follows.
    
    ```bash
    python main.py -u <url> -n <number_of_pages>
    ```
    
    For example, if users would like to crawl 30 pages from the website https://www.cse.ust.hk/~kwtleung/COMP4321/testpage.htm,
    one can run the following command.
    
    ```bash
    python main.py -u https://www.cse.ust.hk/~kwtleung/COMP4321/testpage.htm -n 30
    ```
    If users run the program directly without passing any arguments, the program will crawl 30 pages from the website https://www.cse.ust.hk/~kwtleung/COMP4321/testpage.htm.

    The data is then stored into the database. For database schema, please refer to `schema.pdf`.

6. Run the test program to generate spider_result.txt file from database.

    ```bash
    python main.py -t
    ```
   
   If database is not detected, the program will first crawl the page with default setting, before generating spider_result.txt file from database.