import json
import os
import shutil

# List partial files.
def listPartialFiles(partialsFolder):
    paths = []
    for name in os.listdir(partialsFolder):
        if name.startswith("partial_") and name.endswith(".txt"):
            fullPath = os.path.join(partialsFolder, name)
            paths.append(fullPath)
    paths.sort()
    return paths

# Split a line into a term and a body.
def splitLine(line):
    line = line.rstrip("\n")
    if line == "":
        return "", ""
    parts = line.split("\t", 1)
    if len(parts) == 1:
        return parts[0], ""
    return parts[0], parts[1]

# Merge two sorted partial files.
def mergeTwoFiles(fileLeft, fileRight, fileOut):
    left = open(fileLeft, "r", encoding="utf-8")
    right = open(fileRight, "r", encoding="utf-8")
    out = open(fileOut, "w", encoding="utf-8")

    lineLeft = left.readline()
    lineRight = right.readline()

    while lineLeft != "" and lineRight != "":
        termLeft, bodyLeft = splitLine(lineLeft)
        termRight, bodyRight = splitLine(lineRight)

        if termLeft < termRight:
            out.write(lineLeft)
            lineLeft = left.readline()
        elif termLeft > termRight:
            out.write(lineRight)
            lineRight = right.readline()
        else:
            out.write(termLeft + "\t" + bodyLeft + "," + bodyRight + "\n")
            lineLeft = left.readline()
            lineRight = right.readline()

    while lineLeft != "":
        out.write(lineLeft)
        lineLeft = left.readline()
    while lineRight != "":
        out.write(lineRight)
        lineRight = right.readline()

    left.close()
    right.close()
    out.close()

# Merge all partial files into one index.txt.
def mergeAllPartials(partialsFolder, indexPath):
    paths = listPartialFiles(partialsFolder)
    if len(paths) == 0:
        print("No partial files in", partialsFolder)
        return False

    print("Merging", len(paths), "partial file(s) on disk...")

    if len(paths) == 1:
        shutil.copy2(paths[0], indexPath)
        return True

    current = paths[0]
    tempA = os.path.join(partialsFolder, "mergeA.txt")
    tempB = os.path.join(partialsFolder, "mergeB.txt")
    useA = True
    i = 1
    while i < len(paths):
        if useA:
            outPath = tempA
        else:
            outPath = tempB
        mergeTwoFiles(current, paths[i], outPath)
        if current != paths[0] and os.path.isfile(current):
            os.remove(current)
        current = outPath
        useA = not useA
        i = i + 1

    if os.path.isfile(indexPath):
        os.remove(indexPath)
    shutil.move(current, indexPath)
    if os.path.isfile(tempA):
        os.remove(tempA)
    if os.path.isfile(tempB):
        os.remove(tempB)
    return True

# Read index.txt and write lexicon.txt (return unique term count).
def writeLexicon(indexPath, lexiconPath):
    nTerms = 0
    indexFile = open(indexPath, "rb")
    lexFile = open(lexiconPath, "w", encoding="utf-8")

    while True:
        start_byte = indexFile.tell()
        raw_bytes = indexFile.readline()
        if raw_bytes == b"":
            break

        line = raw_bytes.decode("utf-8", errors="replace").rstrip("\r\n")
        if line == "" or "\t" not in line:
            continue
        
        term = line.split("\t", 1)[0]
        lexFile.write(term + "\t" + str(start_byte) + "\n")
        nTerms = nTerms + 1

    indexFile.close()
    lexFile.close()
    return nTerms

# Finish the index by merging partial files and writing stats.json.
def finishIndex(outputDir, nDocuments, corpus="", partialsFolder=None):
    os.makedirs(outputDir, exist_ok=True)
    indexPath = os.path.join(outputDir, "index.txt")
    lexiconPath = os.path.join(outputDir, "lexicon.txt")

    if partialsFolder is None:
        partialsFolder = os.path.join(outputDir, "partials")
    ok = mergeAllPartials(partialsFolder, indexPath)
    if not ok:
        return None
    nTerms = writeLexicon(indexPath, lexiconPath)

    print("Wrote", indexPath)
    print("Wrote", lexiconPath)
    print("Unique stemmed terms:", nTerms)

    totalBytes = 0
    if os.path.isfile(indexPath):
        totalBytes = totalBytes + os.path.getsize(indexPath)
    if os.path.isfile(lexiconPath):
        totalBytes = totalBytes + os.path.getsize(lexiconPath)
    docIdsPath = os.path.join(outputDir, "doc_ids.txt")
    if os.path.isfile(docIdsPath):
        totalBytes = totalBytes + os.path.getsize(docIdsPath)

    indexKb = round(totalBytes / 1024, 2)
    stats = {
        "corpus": corpus,
        "n_documents_indexed": nDocuments,
        "n_unique_terms": nTerms,
        "index_total_kb": indexKb,
    }
    statsPath = os.path.join(outputDir, "stats.json")
    statsFile = open(statsPath, "w", encoding="utf-8")
    json.dump(stats, statsFile, indent=2)
    statsFile.close()
    print("Wrote", statsPath)
    print("Total index size (KB):", indexKb)

    return stats
