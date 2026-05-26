import json
import os
import sys
import time

from corpus_io import get_url, read_urls
from index_reader import line_for_term, read_lexicon
from parse_document import stem_query
from postings import parse_line
from query import idf, intersect_many, ranked_pairs

def read_stats(index_dir):
    path = os.path.join(str(index_dir), "stats.json")
    if not os.path.isfile(path):
        return None
    f = open(path, encoding="utf-8")
    d = json.load(f)
    f.close()
    return d

def run_query(lex, index_path, urls, text, n_docs):
    stems = stem_query(text)
    if len(stems) == 0:
        print("No terms.")
        return

    lists = []
    tf_maps = []
    for s in stems:
        raw = line_for_term(lex, index_path, s)
        if raw is None:
            print("No results.")
            return
        posts = parse_line(raw)[1]
        if len(posts) == 0:
            print("No results.")
            return
        lists.append(posts)
        m = {}
        for p in posts:
            m[p.docid] = p.frequency
        tf_maps.append(m)

    matched = intersect_many(lists)
    if len(matched) == 0:
        print("No results.")
        return

    N = n_docs
    if N is None or N < 1:
        N = len(urls)
    if N < 1:
        N = 1

    idfs = []
    for posts in lists:
        idfs.append(idf(N, len(posts)))

    t0 = time.perf_counter()
    ordered = ranked_pairs(matched, tf_maps, idfs)
    ms = (time.perf_counter() - t0) * 1000.0

    show = ordered[: min(5, len(ordered))]
    n_show = len(show)

    print("Found " + str(len(matched)) + " doc(s). Top " + str(n_show) + " URLs: (" + str(round(ms, 1)) + " ms)")

    for j in range(len(show)):
        sc, doc_id = show[j]
        url = get_url(urls, doc_id)
        if url is None:
            url = "(no url)"
        print("[" + str(round(sc, 4)) + "] " + url)


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
        print("Usage: python search.py [--index-dir path]")
        sys.exit(1)

    print("Loading...")
    lex = read_lexicon(index_dir)
    urls = read_urls(index_dir)
    stats = read_stats(index_dir)
    n_docs = None
    if stats is not None and stats.get("n_documents_indexed") is not None:
        n_docs = int(stats["n_documents_indexed"])

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
        run_query(lex, index_path, urls, line, n_docs)

if __name__ == "__main__":
    main()
