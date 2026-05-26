import json
import sys
import warnings
from collections import Counter

from bs4 import BeautifulSoup, MarkupResemblesLocatorWarning, XMLParsedAsHTMLWarning
from nltk.stem import PorterStemmer

warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)
warnings.filterwarnings("ignore", category=MarkupResemblesLocatorWarning)

stemmer = PorterStemmer()

TITLE_EXTRA = 5
HEAD_EXTRA = 3
BOLD_EXTRA = 2

def tokenize(text):
    tokens = []
    current = ""
    for ch in text:
        if ch.isalnum() and ch.isascii():
            current = current + ch.lower()
        else:
            if current != "":
                tokens.append(current)
                current = ""
    if current != "":
        tokens.append(current)
    return tokens

def stem_counts(text):
    counts = Counter()
    for word in tokenize(text):
        stem = stemmer.stem(word.lower())
        counts[stem] = counts[stem] + 1
    return counts

def make_soup(document):
    if isinstance(document, dict):
        html = document.get("content", "") or ""
    else:
        html = str(document)
    if not isinstance(html, str):
        html = str(html)

    try:
        soup = BeautifulSoup(html, "lxml")
    except Exception:
        soup = BeautifulSoup(html, "html.parser")

    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()

    return soup

def Parse(document):
    soup = make_soup(document)
    text = soup.get_text(" ", strip=True)
    return tokenize(text)

def weighted_counts(document):
    soup = make_soup(document)

    body_text = soup.get_text(" ", strip=True)
    total = stem_counts(body_text)

    title_text = ""
    if soup.title:
        title_text = soup.title.get_text(" ", strip=True)

    heading_text = ""
    for h in soup.find_all(["h1", "h2", "h3"]):
        heading_text = heading_text + " " + h.get_text(" ", strip=True)

    bold_text = ""
    for b in soup.find_all(["b", "strong"]):
        bold_text = bold_text + " " + b.get_text(" ", strip=True)

    for stem, n in stem_counts(title_text).items():
        total[stem] = total[stem] + TITLE_EXTRA * n

    for stem, n in stem_counts(heading_text).items():
        total[stem] = total[stem] + HEAD_EXTRA * n

    for stem, n in stem_counts(bold_text).items():
        total[stem] = total[stem] + BOLD_EXTRA * n

    return total

def stem_query(query):
    if query is None or query == "":
        return []
    if not isinstance(query, str):
        return []

    words = tokenize(query)
    stems = []
    for word in words:
        stems.append(stemmer.stem(word.lower()))
    return stems
