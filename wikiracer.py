#!/usr/bin/env python
"""
wikiracer.py -

Finds the shortest link between two Wikipedia articles.
"""
import argparse
from itertools import chain
from multiprocessing import Pool
import urllib.request

from bs4 import BeautifulSoup, SoupStrainer

WIKI_URL = 'https://en.wikipedia.org'


class Collection(object):
    """Lightweight wrapper around an arbitrary iterable.

    Update interface enables one-line re-assignment to
    underlying iterable while maintaining a reference to
    wrapper; useful for preserving references.
    """
    def __init__(self, iterable=None):
        if iterable is None:
            self._container = []
        self._container = iterable

    def update(self, new_values):
        self._container = new_values

    def __iter__(self):
        return iter(self._container)

    def __len__(self):
        return len(self._container)


def fetch_url(url: str) -> str:
    """Fetch URL contents and return raw HTML page."""
    try:
        return urllib.request.urlopen(url, timeout=2).read().decode('utf-8')
    except urllib.error.HTTPError:
        return ''


def collect_wiki_links(page: str):
    """Collect all internal Wikipedia links froma raw HTML page."""
    links = set()
    for link in BeautifulSoup(
            page, features='html.parser', parse_only=SoupStrainer('a')):
        if link.has_attr('href'):
            if link['href'].startswith('/wiki/'):
                links.add(link['href'])
    return links


def check_links(start_stub: str, end_stub: str):
    """A coroutine that checks and receives link stubs.
    Unseen stubs are yielded as 'complete' URLs, and if
    the target URL stub is observed then coroutine flow
    is returned, yielding a StopIteration error, which
    in turn terminates the search.
    """
    seen_urls = {"".join([WIKI_URL, start_stub])}
    urls_to_scrape = list(seen_urls)
    depth_counter = 1
    while True:
        new_urls = yield urls_to_scrape
        print("Number of new URLs: {}".format(len(new_urls)))
        if end_stub in new_urls:
            return depth_counter
        depth_counter += 1
        new_urls -= seen_urls
        seen_urls |= new_urls
        urls_to_scrape = list(map(lambda u: "".join([WIKI_URL, u]), new_urls))


def main_loop(start_suffix: str, end_suffix: str):
    """Core control loop for fetching, scraping,
    checking and filtering URLs.
    """
    # Initialize pool of workers for fetching and scraping URLs.
    pool = Pool(processes=4)
    # Initialize checker coroutine and URLs/pages collections
    checker = check_links(start_suffix, end_suffix)
    urls = Collection(next(checker))
    pages = Collection()
    # Flow for fetching URLs and scraping them from pages
    # is identical, and thus can be looped use local refs.
    fetch_scrape_flow = [
        (fetch_url, urls, pages),
        (collect_wiki_links, pages, urls)
    ]
    while True:
        # Fetch pages for URLs, and then scrape new URLs from those pages
        for func, in_collection, out_collection in fetch_scrape_flow:
            handler = pool.map_async(func, in_collection)
            handler.wait()
            out_collection.update(handler.get())
        try:
            # Check new URLs to see if the target URL has been
            # scraped. If not, yield unseen, ready to fetch URLs.
            new_urls = checker.send(set(chain.from_iterable(urls)))
            urls.update(new_urls)
        except StopIteration as exc:
            print("Target found at search depth: {}".format(exc.value))
            break


def build_parser():
    """Build CLI argparser."""
    parser = argparse.ArgumentParser(epilog=__doc__)
    parser.add_argument(
        'start_suffix', type=str, metavar='/wiki/<start-article-name>',
        help="Suffix of starting article.")
    parser.add_argument(
        'end_suffix', type=str, metavar='/wiki/<end-article-name>',
        help="Suffix of starting article.")

    return parser


if __name__ == "__main__":
    parser = build_parser()
    cli_args = parser.parse_args()
    main_loop(cli_args.start_suffix, cli_args.end_suffix)
