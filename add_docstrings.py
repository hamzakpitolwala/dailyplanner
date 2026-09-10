import ast
import os
import glob
import textwrap

def generate_docstring(name):
    # e.g., get_user_by_id -> Get user by id.
    words = name.split('_')
    words[0] = words[0].capitalize()
    return " ".join(words) + "."

def add_docstrings(filepath):
    with open(filepath, "r") as f:
        source = f.read()
    
    tree = ast.parse(source)
    lines = source.splitlines()
    
    # We will insert docstrings from bottom to top so line numbers don't shift
    insertions = {}
    
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            if not ast.get_docstring(node):
                doc = generate_docstring(node.name)
                # Find the first line after the function signature
                # node.body[0].lineno is the 1-indexed line of the first statement
                target_line = node.body[0].lineno - 1
                
                # We need to find the correct indentation
                indent = " " * node.body[0].col_offset
                doc_str = f'{indent}"""{doc}"""'
                insertions[target_line] = doc_str

    if not insertions:
        return False
        
    for line_idx in sorted(insertions.keys(), reverse=True):
        lines.insert(line_idx, insertions[line_idx])
        
    with open(filepath, "w") as f:
        f.write("\n".join(lines) + "\n")
    return True

if __name__ == "__main__":
    count = 0
    for filepath in glob.glob("backend/**/*.py", recursive=True):
        if "venv" in filepath or "__pycache__" in filepath:
            continue
        try:
            if add_docstrings(filepath):
                print(f"Added docstrings to {filepath}")
                count += 1
        except Exception as e:
            print(f"Error processing {filepath}: {e}")
            
    print(f"Processed {count} files.")
