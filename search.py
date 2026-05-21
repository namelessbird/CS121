import os
import sys

from corpus_io import get_url, read_urls
from index_reader import line_for_term, read_lexicon
from parse_document import stem_query
from postings import parse_line
from query import intersect


def run_query(lex, index_path, urls, text):
    stems = stem_query(text)
    if len(stems) == 0:
        print("No terms.")
        return

    lists = []
    for s in stems:
        raw = line_for_term(lex, index_path, s)
        if raw is None:
            print("No results.")
            return
        parsed = parse_line(raw)
        posts = parsed[1]
        if len(posts) == 0:
            print("No results.")
            return
        lists.append(posts)

    matched = lists[0]
    k = 1
    while k < len(lists):
        matched = intersect(matched, lists[k])
        k = k + 1

    if len(matched) == 0:
        print("No results.")
        return

    print("Found", len(matched), "doc(s). Top 5:")
    how_many = 5
    if len(matched) < how_many:
        how_many = len(matched)
    j = 0
    while j < how_many:
        doc_id = matched[j].docid
        url = get_url(urls, doc_id)
        if url is None:
            url = "(no url)"
        print(" ", j + 1, url)
        j = j + 1


def main():
    index_dir = os.path.join("..", "index", "dev-all")

    arg_i = 1
    while arg_i < len(sys.argv):
        if sys.argv[arg_i] == "--index-dir" and arg_i + 1 < len(sys.argv):
            index_dir = sys.argv[arg_i + 1]
            arg_i = arg_i + 2
        else:
            arg_i = arg_i + 1

    index_path = os.path.join(index_dir, "index.txt")
    if not os.path.isfile(index_path):
        print("Missing:", index_path)
        print("Usage: python search.py [--index-dir path\\to\\index]")
        sys.exit(1)

    print("Loading...")
    lex = read_lexicon(index_dir)
    urls = read_urls(index_dir)
    print("Ready (quit to exit).\n")

    while True:
        try:
            line = input("> ").strip()
        except EOFError:
            print()
            break
        if line == "":
            continue
        low = line.lower()
        if low == "quit" or low == "exit" or low == "q":
            break
        run_query(lex, index_path, urls, line)
