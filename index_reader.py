import os
import sys

# lexicon.txt -> dict word -> byte offset in index.txt
def read_lexicon(index_dir):
    path = os.path.join(str(index_dir), "lexicon.txt")
    lex = {}
    f = open(path, encoding="utf-8")
    for line in f:
        line = line.rstrip("\r\n")
        if line == "":
            continue
        parts = line.split("\t", 1)
        if len(parts) < 2:
            continue
        word = parts[0]
        offset = int(parts[1])
        lex[word] = offset
    f.close()
    return lex

# read one line from index.txt at byte offset
def read_index_line(index_path, offset):
    f = open(index_path, "rb")
    f.seek(offset)
    raw = f.readline()
    f.close()
    if raw == b"":
        return ""
    text = raw.decode("utf-8", errors="replace")
    return text.rstrip("\r\n")

def line_for_term(lex, index_path, term):
    if term not in lex:
        return None
    off = lex[term]
    return read_index_line(index_path, off)
