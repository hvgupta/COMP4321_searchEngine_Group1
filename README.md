# This project has been created by Group 1 for the course COMP 4321 (24S)

## Project Phase 1

The project is based on Python, version ***3.11.0***. The project uses the following packages:

- To be filled

It is expected that users will execute the command on a **_Linux-based_** operating system, with bash / zsh as the shell.

To run the test program, users should do the following. 

0. Users need to ensure they have installed the correct python version. 

1. Create a virtual environment using the following command. 

```bash
python -m venv venv
```

2. Activate the virtual environment using the following command.

```bash
source venv/bin/activate
```

3. Install the required package

```bash
pip install -r requirements.txt
```

4. Run the test program using the following command. (This is for phase 1 only.)

    The test program consists of two inputs, which are the url of the website to be crawled, and
    the number of pages to be crawled. The usage is shown as follows.
    
    ```bash
    python main.py -u <url> -n <number_of_pages>
    ```
    
    For example, if users would like to crawl 30 pages from the website https://comp4321-hkust.github.io/testpages/testpage.htm,
    one can run the following command.
    
    ```bash
    python main.py -u https://comp4321-hkust.github.io/testpages/testpage.htm -n 30
    ```
    
    If users run the program directly without passing any arguments, the program will crawl 30 pages from the website https://comp4321-hkust.github.io/testpages/testpage.htm.

![Kenneth](Kenneth.jpg)