import json
import sys
import warnings

from bs4 import BeautifulSoup, MarkupResemblesLocatorWarning, XMLParsedAsHTMLWarning
from nltk.stem import PorterStemmer

warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)
warnings.filterwarnings("ignore", category=MarkupResemblesLocatorWarning)

stemmer = PorterStemmer()

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

def Parse(document):
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

    text = soup.get_text(" ", strip=True)

    return tokenize(text)

# Turn a user query string into stemmed terms
def stem_query(query):
    if query is None or query == "":
        return []
    if not isinstance(query, str):
        return []

    words = tokenize(query)
    stems = []
    for word in words:
        low = word.lower()
        stemmed_word = stemmer.stem(low)
        stems.append(stemmed_word)
    return stems
