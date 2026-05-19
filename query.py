def query():
    pass

def intersect(p1, p2):
    contains = []
    i = 0
    j = 0
    p1_len = len(p1)
    p2_len = len(p2)
    while i < p1_len and j < p2_len:
        if p1[i].docid == p2[j].docid:
            contains.append(p1[i])
            i += 1
            j += 1
        else:
            if p1[i].docid < p2[j].docid:
                i += 1
            else:
                j += 1
    return contains