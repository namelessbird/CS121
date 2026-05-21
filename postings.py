class Postings:
    def __init__(self, docID, frequency, fields="none"):
        self.docid = docID
        self.frequency = frequency
        self.fields = fields

def parse_body(body):
    out = []
    if body is None or body == "":
        return out

    for piece in body.split(","):
        piece = piece.strip()
        if piece == "":
            continue
        parts = piece.split(":")
        doc_id = int(parts[0])
        freq = int(parts[1])
        out.append(Postings(doc_id, freq))
    return out


def parse_line(line):
    line = line.rstrip("\r\n")
    if line == "":
        return "", []

    if "\t" not in line:
        return line, []

    term, body = line.split("\t", 1)
    return term, parse_body(body)
