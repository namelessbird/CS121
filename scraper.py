import re
from urllib.parse import urlparse, urljoin, urldefrag
from bs4 import BeautifulSoup
from stats import STATS, tokenize

ALLOWED_DOMAINS = (
    "ics.uci.edu",
    "cs.uci.edu",
    "informatics.uci.edu",
    "stat.uci.edu",
)

MIN_WORDS_PER_PAGE = 50

BAD_EXTENSIONS = re.compile(
    r".*\.("
    r"css|js|json|xml|rss|atom"
    r"|bmp|gif|jpe?g|ico|png|tiff?|svg|webp"
    r"|mp[234]|mid|ram|wav|m4[av]|wma|ogg|flac|aac"
    r"|avi|mov|mpeg|mkv|ogv|webm|wmv|swf|rm|smil"
    r"|pdf|ps|eps|tex|ppt|pptx|ppsx|thmx|mso|rtf|key|odp|ods|odt"
    r"|doc|docx|xls|xlsx|csv|tsv|dat|data|names|arff"
    r"|exe|msi|bin|apk|dll|jar|war|class"
    r"|bz2|tar|gz|tgz|7z|rar|zip|lz|lzma|xz"
    r"|psd|ai|dmg|iso|epub|cnf|sha1|sha256|md5|asc|sig"
    r"|woff2?|ttf|otf|eot|sql|sqlite|db|ipynb|mat|fig|nb"
    r")$",
    re.IGNORECASE,
)

BAD_PATHS = re.compile(
    r"(?:/wp-(?:login|admin|json)|/login|/signup|/signin|/logout|/register"
    r"|/share|/sharer|/replytocom|/feed|/atom|/rss"
    r"|/trackback|/pingback|/embed|/attachment|/cas/login)",
    re.IGNORECASE,
)

BAD_QUERY_PARAMS = frozenset({
    "ical", "outlook-ical", "share", "sharer",
    "action", "do",
    "rev", "revision", "diff", "version", "oldid", "history",
    "redirect_to", "redirect", "replytocom",
    "format", "print", "printable",
    "phpsessid", "sid", "session",
    "filter", "sort_by", "orderby",
    "tribe-bar-date", "eventdate",
})

def scraper(url, resp):
    links = extract_next_links(url, resp)
    return [link for link in links if is_valid(link)]

def extract_next_links(url, resp):
    # Implementation required.
    # url: the URL that was used to get the page
    # resp.url: the actual url of the page
    # resp.status: the status code returned by the server. 200 is OK, you got the page. Other numbers mean that there was some kind of problem.
    # resp.error: when status is not 200, you can check the error here, if needed.
    # resp.raw_response: this is where the page actually is. More specifically, the raw_response has two parts:
    #         resp.raw_response.url: the url, again
    #         resp.raw_response.content: the content of the page!
    # Return a list with the hyperlinks (as strings) scrapped from resp.raw_response.content

    if resp.status != 200 or not resp.raw_response:
        return []
    soup = BeautifulSoup(resp.raw_response.content, "lxml")
    for tag in soup(["script", "style", "noscript", "template"]):
        tag.decompose()
    text = soup.get_text(separator=" ", strip=True)
    tokens = tokenize(text)
    final_url, _ = urldefrag(resp.url or url)
    STATS.record_page(final_url, tokens)
    if len(tokens) >= MIN_WORDS_PER_PAGE:
        text_hash = hashlib.md5(" ".join(tokens).encode("utf-8", "ignore")).hexdigest()
        if STATS.is_duplicate(text_hash):
            return []
        STATS.mark_seen(text_hash)
    links = []
    for anchor in soup.find_all("a", href=True):
        link = anchor.get("href")
        fullURL = urljoin(resp.url, link)
        parsed = urlparse(fullURL)
        notFragmentLink = parsed._replace(fragment="").geturl()
        links.append(notFragmentLink)
    return links

def is_valid(url):
    # Decide whether to crawl this url or not. 
    # If you decide to crawl it, return True; otherwise return False.
    # There are already some conditions that return False.
    try:
        parsed = urlparse(url)
        if parsed.scheme not in set(["http", "https"]):
            return False
        return not re.match(
            r".*\.(css|js|bmp|gif|jpe?g|ico"
            + r"|png|tiff?|mid|mp2|mp3|mp4"
            + r"|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf"
            + r"|ps|eps|tex|ppt|pptx|doc|docx|xls|xlsx|names"
            + r"|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso"
            + r"|epub|dll|cnf|tgz|sha1"
            + r"|thmx|mso|arff|rtf|jar|csv"
            + r"|rm|smil|wmv|swf|wma|zip|rar|gz)$", parsed.path.lower())

    except TypeError:
        print ("TypeError for ", parsed)
        raise
