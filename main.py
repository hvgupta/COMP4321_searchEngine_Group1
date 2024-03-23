import src.crawler as crawler
import argparse


def create_file_from_db():
    with open("spider_result.txt", "w+") as file:
        pass

def main():
    parser = argparse.ArgumentParser()

    parser.add_argument("-n", "--num", dest="NUM_PAGES", default="30",
                        help="Number of pages that will be crawled / indexed")
    parser.add_argument("-u", "--url", dest="URL", default="https://comp4321-hkust.github.io/testpages/testpage.htm",
                        help="The URL that the program will be crawled")
    parser.add_argument("-t", "--test", dest="is_test", action='store_true', required=False,
                        help="Read the database and generate output")

    args = parser.parse_args()

    # Simply replace them with your own URL if you find passing flags into program is complicated.
    # - Number of pages that will be crawled / indexed - 
    MAX_NUM_PAGES = args.NUM_PAGES

    # - The URL that the program will be crawled -
    URL = args.URL

    if not args.is_test:
        crawler.recursively_crawl(num_pages=MAX_NUM_PAGES, url=URL)
    else:
        create_file_from_db()


if __name__ == '__main__':
    main()
