import math

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

def intersect_many(lists):
    if len(lists) == 0:
        return []
    cur = lists[0]
    k = 1
    while k < len(lists):
        cur = intersect(cur, lists[k])
        k = k + 1
    return cur

def idf(N, df):
    if df < 1:
        df = 1
    if N < 1:
        N = 1
    return math.log((N - df + 0.5) / (df + 0.5) + 1.0)

def score_doc(tf_maps, idfs, doc_id, n_terms):
    s = 0.0
    sum_sq = 0.0
    t = 0
    while t < n_terms:
        tf = tf_maps[t].get(doc_id, 0)
        if tf < 1:
            tf = 1
        w = 1.0 + math.log(tf)
        sum_sq = sum_sq + w * w
        s = s + w * idfs[t]
        t = t + 1
    norm = math.sqrt(sum_sq)
    if norm < 1e-12:
        norm = 1.0
    return s / norm

def row_sort_key(row):
    sc = row[0]
    doc_id = row[1]
    return (-sc, doc_id)

def ranked_pairs(matched, tf_maps, idfs):
    rows = []
    for p in matched:
        doc_id = p.docid
        sc = score_doc(tf_maps, idfs, doc_id, len(tf_maps))
        rows.append((sc, doc_id))
    rows.sort(key=row_sort_key)
    return rows
