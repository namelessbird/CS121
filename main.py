import argparse
import os
import sys

from corpus_io import collect_pages, write_doc_ids
from index import buildPartialIndex
from merge_report import finishIndex

# Defaults when you run: python main.py
TEAM_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_CORPUS = os.path.normpath(os.path.join(TEAM_DIR, "..", "developer", "DEV"))
DEFAULT_OUTPUT = os.path.normpath(os.path.join(TEAM_DIR, "..", "index", "dev-all"))

def main():
    # Read command-line options
    parser = argparse.ArgumentParser(description="Indexer milestone 1")
    parser.add_argument(
        "--corpus",
        default=DEFAULT_CORPUS,
        help="Folder with JSON pages (default: ../developer/DEV)",
    )
    parser.add_argument(
        "--output",
        default=DEFAULT_OUTPUT,
        help="Output folder (default: ../index/dev-all; created if missing)",
    )
    parser.add_argument("--limit", type=int, default=None, help="Only load this many pages (for testing)")
    parser.add_argument(
        "--docs-per-partial",
        type=int,
        default=5000,
        help="Write one partial index file after every N pages (default 5000).",
    )
    args = parser.parse_args()

    print("Corpus:", args.corpus)
    print("Output:", args.output)

    # Load pages as [(doc_id, {"url", "content"}), ...]
    print("Reading corpus...")
    pages = collect_pages(args.corpus, limit=args.limit)
    if len(pages) == 0:
        print("No pages found. Check --corpus path.")
        sys.exit(1)

    # Write doc_ids.txt (one line per page: doc_id + tab + url)
    write_doc_ids(args.output, pages)
    print("Loaded", len(pages), "documents.")
    print("Wrote", os.path.join(args.output, "doc_ids.txt"))

    documents = [page for (doc_id, page) in pages]

    # Parse is inside index.py
    partialsFolder = os.path.join(args.output, "partials")
    print("Building partial index files in:", partialsFolder)
    print("(one partial file every", args.docs_per_partial, "pages)")
    partialPaths, sumlengths = buildPartialIndex(
        documents,
        partialsFolder,
        docsPerPartial=args.docs_per_partial,
    )
    print("Wrote", len(partialPaths), "partial index file(s).")
    if len(partialPaths) < 3 and args.limit is None:
        print(
            "Developer spec wants >= 3 partial files on full corpus.",
            "Use a smaller --docs-per-partial if you only see 1 or 2 files.",
        )

    n_pages = len(pages)
    avglength = 0.0
    if n_pages > 0:
        avglength = sumlengths / n_pages

    # Merging partial files
    finishIndex(
        args.output,
        nDocuments=len(pages),
        corpus=os.path.normpath(args.corpus),
        partialsFolder=partialsFolder,
        avglength=avglength,
    )

if __name__ == "__main__":
    main()
