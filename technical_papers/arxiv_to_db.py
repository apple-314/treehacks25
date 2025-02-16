import json
import re
from vector_db import VectorDatabase

def preprocess_tex_file(input_file):
    with open(input_file, 'r') as tex_file:
        tex_content = tex_file.readlines()

    # Step 1: Remove comments (lines where first non-whitespace character is %)
    tex_content = [line for line in tex_content if not re.match(r'^\s*%', line)]
    tex_content = ''.join(tex_content)  # Convert back to a single string

    # Step 2: Remove LaTeX formatting commands (like \textbf{}, \emph{})
    tex_content = re.sub(r'\\(textbf|emph|textit|underline|section|subsection|texttt|textit|mathsf|mathbf){[^}]+}', '', tex_content)

    # Step 3: Remove equations and math environments
    tex_content = re.sub(r'\\\([^\\]*\\\)', ' [math eq] ', tex_content)  # Inline math \( ... \)
    tex_content = re.sub(r'\$[^$]*\$', ' [math eq] ', tex_content)  # Inline math $ ... $
    tex_content = re.sub(r'\\\[.*?\\\]', ' [math eq] ', tex_content, flags=re.DOTALL)  # Displayed equations

    # Step 4: Remove unwanted environments
    environments_to_remove = ['figure', 'align\*', 'tabular', 'table', 'equation', 'equation\*', 'align']
    for env in environments_to_remove:
        tex_content = re.sub(rf'\\begin{{{env}}}.*?\\end{{{env}}}', f' [{env[:3]}] ', tex_content, flags=re.DOTALL)
    
    tex_content = re.sub(r'\\begin{figure\*}[\s\S]*?\\end{figure\*}', ' [fig*] ', tex_content)

    # Step 5: Remove usepackage and new command stuff
    tex_content = re.sub(r'\\usepackage{[^}]+}', '', tex_content)
    tex_content = re.sub(r'\\newcommand{[^}]+}{[^}]+}', '', tex_content)
    
    return tex_content

def main():
    db = VectorDatabase()
    db.create_connection()

    db.delete_schema("TechnicalAgent")
    
    # get json of all arxiv papers already parsed
    with open("arxiv_metadata.json", "r", encoding="utf-8") as f:
        arxiv_metadata = json.load(f)
    
    id_title = {}
    for x in arxiv_metadata:
        id_title[x["arxiv_id"]] = x["title"]
    
    for x in id_title:
        print(f"{x}: {id_title[x]}")
    print()

    x = 1
    for id in id_title:
        # f = open(f"arxiv_tex_text/{id}.txt", "r", encoding="utf-8")
        # l = f.readlines()
        # s = "\n".join(l)
        # f.close()

        s = preprocess_tex_file(f"arxiv_tex_text/{id}.txt")
        d = {"title": id_title[id], "arxiv_id": id}
        print(f"paper {x}: {d}")
        x += 1

        db.add_text_to_table("TechnicalAgent", "Documents", s, 512, d)
    
main()