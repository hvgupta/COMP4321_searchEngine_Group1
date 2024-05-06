import sqlite3
import datetime
from pathlib import Path
from collections import Counter, defaultdict
from typing import Dict

# Connect to the documents database
db_path = str(Path.cwd()) + '/src/files/database.db'
connection = sqlite3.connect(db_path, check_same_thread=False)  # Set check_same_thread to False because Flask initialized the connection in a different thread, this is safe because the search engine is read only
cursor = connection.cursor()

def page_id_to_page_info(id: int) -> tuple[str, int, int]:
    """
    Get a page's entry in table page_info (title, size, last modified time) from its ID.

    Parameters
    -----------
    id: :class:`int`
        The ID of the page.
    
    Returns
    --------
    :class:`tuple[str, int, int]`
        Tuple containing title, size, last modified time of the page.
    
    Raises
    -------
    ValueError
        No page with the given ID is found.
    """

    # Find entry in table
    page_info: tuple[str, int, int] = cursor.execute("SELECT title, last_mod_date, size FROM page_info WHERE page_id = ?", (id,)).fetchone()

    # Raise error if no page found
    if page_info is None:
        raise ValueError("No page with the given ID is found.")
    
    return page_info

def page_id_to_url(id: int) -> str:
    """
    Get a page's entry in table id_url (URL) from its ID.

    Parameters
    -----------
    id: :class:`int`
        The ID of the page.
    
    Returns
    --------
    :class:`str`
        The URL of the actual page on the remote server.
    
    Raises
    -------
    ValueError
        No page with the given ID is found.
    """

    # Find entry in table
    url: tuple[str] = cursor.execute("SELECT url FROM id_url WHERE page_id = ?", (id,)).fetchone()

    # Raise error if no page found
    if url is None:
        raise ValueError("No page with the given ID is found.")

    # The entry is a tuple, flatten it before returning
    return url[0]

def page_id_to_stems(id: int, num_stems: int = 5, include_title: bool = True) -> list[tuple[str, int]]:
    """
    Get the `num_stems` most frequent stemmed keywords of a page from its ID.

    Parameters
    -----------
    id: :class:`int`
        The ID of the page.
    num_stems: :class:`int`
        Number of stems to return.
    include_title: :class:`bool`
        Whether to include the title when counting the stems.

    Returns
    --------
    :class:`list[tuple[str, int]]`
        A list of tuples containing a stem and its frequency in the page.

    Raises
    -------
    ValueError
        No page with the given ID is found.
    """

    # Get list of all stems in the document
    stems_freqs: list[tuple[int, int]] = list(cursor.execute("SELECT word_id, count FROM inverted_idx WHERE page_id = ?", (id,)))
    if include_title:
        stems_freqs += list(cursor.execute("SELECT word_id, count FROM title_inverted_idx WHERE page_id = ?", (id,)))
    
    # Raise error if no page found
    if stems_freqs is None:
        raise ValueError("No page with the given ID is found.")
    
    # Convert stem word IDs to stems
    stems_ids: list[int] = [stem[0] for stem in stems_freqs]
    freqs: list[int] = [stem[1] for stem in stems_freqs]
    stems: list[str] = []
    for stem_id in stems_ids:
        stem: str = cursor.execute("SELECT word FROM word_id_word WHERE word_id = ?", (stem_id,)).fetchone()[0]
        stems.append(stem)

    # Combine stems and counts
    stems_counts: list[tuple[str, int]] = list(zip(stems, freqs))

    # Merge the keyword together
    d = defaultdict(int)

    for k, v in stems_counts:
        d[k] += v

    stems_counts = list(d.items())

    # Sort and filter to get `num_stems` most frequent stems
    return sorted(stems_counts, key=lambda x: x[1], reverse=True)[0: num_stems]

def page_id_to_links(id: int, parent: bool = True) -> list[str]:
    """
    Get the parent/child links of a page from its ID.

    Parameters
    -----------
    id: :class:`int`
        The ID of the page.
    parent: :class:`bool`
        If true, search for parent links. Otherwise, search for child links.
    
    Returns
    --------
    :class:`list[str]`
        List of parent/child links of the page.
    """

    # Get linked page IDs
    link_ids: list[tuple[int]] = []
    if parent:
        link_ids = cursor.execute("SELECT parent_id FROM relation WHERE child_id = ?", (id,)).fetchall()
    else:
        link_ids = cursor.execute("SELECT child_id FROM relation WHERE parent_id = ?", (id,)).fetchall()
    
    # Convert ID of each linked page to its URL
    links: list[str] = []
    for link_id in link_ids:
        link_id_flat: int = link_id[0]  # Extract ID from its containing tuple
        try:
            links.append(page_id_to_url(link_id_flat))
        except ValueError:  # Handle first page which has no parent
            pass
    
    return links

def timestamp_to_datetime(timestamp: int):
    """
    Convert UNIX timestamp to ISO 8601 date and [hh]:[mm]:[ss] time.

    Parameters
    -----------
    timestamp: :class:`int`
        The UNIX timestamp to be converted.
    """

    dt = datetime.datetime.fromtimestamp(timestamp)

    return dt.strftime("%Y-%m-%d %H:%M:%S")

class SearchResult:
    """
    Represents a document retrieved by the search engine.

    Attributes
    -----------
    id: :class:`int`
        The ID of the document.
    score: :class:`float`
        The score of the document.
    title: :class:`str`
        The title of the document.
    time: :class:`int`
        The last modified time of the document.
    time_formatted: :class:`str`
        The last modified time of the document, formatted to string.
    size: :class:`int`
        The size of the document.
    url: :class:`str`
        The URL of the document.
    keywords: :class:`list[tuple[str, int]]`
        The 5 most frequent stemmed keywords (excluding stopwords) in the document, together with their occurence frequencies.
    parent_links: :class:`list[str]`
        The parent links of the document.
    child_links: :class:`list[str]`
        The child links of the document.
    """

    def __init__(self, id: int, score: float, num_keywords: int = 5):
        """
        Inits SearchResult.

        Parameters
        -----------
        num_keywords: :class:`int`
            Controls how many stemmed keywords in the document to be included. Defaults to 5.
        """

        # Initialize ID and score (given)
        self.id: int = id
        self.score: float = score

        # Initialize document title, last modified time, size
        page_info: tuple[str, int, int] = page_id_to_page_info(id)
        self.title: str = page_info[0]
        self.time: int = page_info[1]
        self.size: int = page_info[2]

        # Format last modified time
        self.time_formatted: str = timestamp_to_datetime(self.time)

        # Initialize document URL
        self.url: str = page_id_to_url(id)

        # Initialize most frequent stemmed keywords
        self.keywords: list[tuple[str, int]] = page_id_to_stems(id)

        # Initialize parent links
        self.parent_links: list[str] = page_id_to_links(id, parent=True)

        # Initialize child links
        self.child_links: list[str] = page_id_to_links(id, parent=False)