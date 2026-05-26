import os

from parse_document import weighted_counts
from postings import Postings

def writePartialFile(index, partialsFolder, partialNum, paths):
    if len(index) == 0:
        return index, partialNum, paths

    fileNum = str(partialNum).zfill(4)
    path = os.path.join(partialsFolder, "partial_" + fileNum + ".txt")
    f = open(path, "w", encoding="utf-8")
    for term in sorted(index.keys()):
        posts = index[term]
        line = term + "\t" + ",".join(str(p.docid) + ":" + str(p.frequency) for p in posts)
        f.write(line + "\n")
    f.close()

    paths.append(path)
    return {}, partialNum + 1, paths

def buildIndex(documents):
    index = {}
    docNum = -1

    for document in documents:
        docNum = docNum + 1
        counts = weighted_counts(document)

        for token, freq in counts.items():
            freq_i = int(freq)
            if freq_i < 1:
                freq_i = 1
            tempPost = Postings(docNum, freq_i)
            if token not in index:
                index[token] = [tempPost]
            else:
                index[token].append(tempPost)

    return index

def buildPartialIndex(documents, partialsFolder, docsPerPartial=5000):
    os.makedirs(partialsFolder, exist_ok=True)

    index = {}
    nDocs = 0
    partialNum = 0
    paths = []
    docNum = -1
    sumlengths = 0

    for document in documents:
        docNum = docNum + 1
        counts = weighted_counts(document)

        doc_len = 0
        for token, freq in counts.items():
            freq_i = int(freq)
            if freq_i < 1:
                freq_i = 1
            doc_len = doc_len + freq_i
            tempPost = Postings(docNum, freq_i)
            if token not in index:
                index[token] = [tempPost]
            else:
                index[token].append(tempPost)

        sumlengths = sumlengths + doc_len

        nDocs = nDocs + 1
        if nDocs >= docsPerPartial:
            index, partialNum, paths = writePartialFile(index, partialsFolder, partialNum, paths)
            nDocs = 0

        if docsPerPartial > 0 and docNum > 0 and (docNum + 1) % docsPerPartial == 0:
            print("  ... indexed", docNum + 1, "documents (partial files so far:", len(paths), ")")

    index, partialNum, paths = writePartialFile(index, partialsFolder, partialNum, paths)
    return paths, sumlengths
