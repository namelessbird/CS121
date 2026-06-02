import FreeSimpleGUI as sg

from search import read_lexicon, read_stats, read_urls, run_query
import sys, io, os


index_dir = os.path.join("..", "index", "dev-all")
lex, urls = read_lexicon(index_dir), read_urls(index_dir)
stats = read_stats(index_dir)
n_docs = int(stats["n_documents_indexed"]) if stats and "n_documents_indexed" in stats else None


layout = [
    [sg.Text("Enter search terms:"), sg.Input(key="-QUERY-", do_not_clear=True), sg.Button("Search", bind_return_key=True)],
    [sg.Multiline(size=(80, 20), key="-OUTPUT-", font=("Courier", 10), disabled=True)],
    [sg.Button("Exit")]
]


window = sg.Window("Search Engine", layout)


while True:
    event, values = window.read()
    if event in (sg.WIN_CLOSED, "Exit"):
        break
        
    if event == "Search":
        query_text = values["-QUERY-"].strip()
        if query_text:
            
            old_stdout = sys.stdout
            sys.stdout = buffer = io.StringIO()
            
            run_query(lex, os.path.join(index_dir, "index.txt"), urls, query_text, n_docs)
            
            sys.stdout = old_stdout
            window["-OUTPUT-"].update(buffer.getvalue())

window.close()