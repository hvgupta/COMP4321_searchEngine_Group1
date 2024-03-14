import src.crawler as crawler
import argparse


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument("-n", "--numpages", dest = "NUM_PAGES", default = "30", help="Number of pages that will be crawled / indexed")
    parser.add_argument("-u", "--url", dest = "URL", default = "https://comp4321-hkust.github.io/testpages/testpage.htm", help="The URL that the program will be crawled")

    args = parser.parse_args()

    # Simply replace them with your own URL if you find passing flags into program is complicated.
    # - Number of pages that will be crawled / indexed - 
    MAX_NUM_PAGES = args.NUM_PAGES

    # - The URL that the program will be crawled -
    URL = args.URL



if __name__ == '__main__':
    main()