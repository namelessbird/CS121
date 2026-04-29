import re
from urllib.parse import urlparse, urljoin, urldefrag, parse_qsl
from bs4 import BeautifulSoup
from stats import STATS, tokenize

ALLOWED_DOMAINS = (
    "ics.uci.edu",
    "cs.uci.edu",
    "informatics.uci.edu",
    "stat.uci.edu",
)

MAX_URL_LENGTH = 300
MAX_PATH_DEPTH = 10
MAX_QUERY_PARAMS = 6
MAX_PAGE_SIZE = 8 * 1024 * 1024
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

    if 300 <= resp.status < 400:
        headers = getattr(resp.raw_response, "headers", None) or {}
        location = headers.get("Location") or headers.get("location")
        if not location:
            return []
        target, _ = urldefrag(urljoin(url, location.strip()))
        return [target] if target else []

    if resp.status != 200 or not resp.raw_response:
        return []
    if not resp.raw_response.content:
        return []
    if len(resp.raw_response.content) > MAX_PAGE_SIZE:
        return []
    soup = BeautifulSoup(resp.raw_response.content, "lxml")
    for tag in soup(["script", "style", "noscript", "template"]):
        tag.decompose()
    text = soup.get_text(separator=" ", strip=True)
    tokens = tokenize(text)
    final_url, _ = urldefrag(resp.url or url)
    if not _in_scope(final_url):
        return []
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
    except ValueError:
        return False
    if parsed.scheme not in ("http", "https"):
        return False
    if not _in_scope(url):
        return False
    if len(url) > MAX_URL_LENGTH:                          
        return False
    path = parsed.path or "/"
    if BAD_EXTENSIONS.match(path):
        return False
    if BAD_PATHS.search(path):
        return False
    parts = [s for s in path.split("/") if s]              
    if len(parts) > MAX_PATH_DEPTH:                       
        return False
    if parsed.query:
        try:
            params = parse_qsl(parsed.query, keep_blank_values=True)
        except ValueError:
            return False
        if len(params) > MAX_QUERY_PARAMS:                 
            return False
        for key, _ in params:
            if key.lower() in BAD_QUERY_PARAMS:
                return False
    return True

def _in_scope(url):
    host = (urlparse(url).hostname or "").lower()
    return any(host == d or host.endswith("." + d) for d in ALLOWED_DOMAINS)
