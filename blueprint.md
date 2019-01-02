# Core actors

- Scraper: scrapes URLs from HTML files.
- Fetcher: fetches HTMLs and adds them to scraper queue.

# Algorithm

1. BFS until a path is found.
    - Path is guaranteed to be shortest.

# Considerations

- Use a set-like structure to track observed URLs.
- Can I use a cyclic stream structure like-structure
    such as Kafta to connect the scrapers and fetchers?
