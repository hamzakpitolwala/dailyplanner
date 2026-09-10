import os
import glob
import re

def generate_docstring(name):
    # e.g., fetchTasks -> Fetch tasks.
    # CamelCase to readable:
    words = re.sub('([a-z0-9])([A-Z])', r'\1 \2', name).split()
    if not words:
        return ""
    words[0] = words[0].capitalize()
    return " ".join(words) + "."

def add_docstrings(filepath):
    with open(filepath, "r") as f:
        source = f.read()
    
    lines = source.splitlines()
    insertions = {}
    
    # Simple regex for exported functions and components
    # e.g., export const fetchTasks = async (targetDate) => {
    # e.g., export default function PlannerTimeline() {
    # e.g., const PlannerTimeline = () => {
    
    patterns = [
        re.compile(r'^(\s*)export\s+(?:const|let|var)\s+([a-zA-Z0-9_]+)\s*=\s*(?:async\s*)?(?:\([^)]*\)|[a-zA-Z0-9_]+)\s*=>'),
        re.compile(r'^(\s*)export\s+default\s+function\s+([a-zA-Z0-9_]+)\s*\('),
        re.compile(r'^(\s*)export\s+function\s+([a-zA-Z0-9_]+)\s*\('),
        re.compile(r'^(\s*)const\s+([a-zA-Z0-9_]+)\s*=\s*(?:async\s*)?(?:\([^)]*\)|[a-zA-Z0-9_]+)\s*=>'),
        re.compile(r'^(\s*)function\s+([a-zA-Z0-9_]+)\s*\(')
    ]
    
    skip_next = False
    
    for i, line in enumerate(lines):
        if skip_next:
            skip_next = False
            continue
            
        # check if it already has a comment
        if i > 0 and (lines[i-1].strip().endswith('*/') or lines[i-1].strip().startswith('//')):
            continue
            
        for p in patterns:
            match = p.search(line)
            if match:
                indent = match.group(1)
                name = match.group(2)
                doc = generate_docstring(name)
                # Ensure we only insert once per line
                if i not in insertions:
                    insertions[i] = f"{indent}/**\n{indent} * {doc}\n{indent} */"
                break
                
    if not insertions:
        return False
        
    for line_idx in sorted(insertions.keys(), reverse=True):
        lines.insert(line_idx, insertions[line_idx])
        
    with open(filepath, "w") as f:
        f.write("\n".join(lines) + "\n")
    return True

if __name__ == "__main__":
    count = 0
    dirs_to_check = [
        "frontend/src/api/**/*.js",
        "frontend/src/api/**/*.ts",
        "frontend/src/contexts/**/*.jsx",
        "frontend/src/contexts/**/*.tsx",
        "frontend/src/components/Planner/**/*.jsx",
        "frontend/src/components/Planner/**/*.tsx",
        "frontend/src/components/Planner/**/*.ts",
        "frontend/src/components/PlannerAI/**/*.tsx",
        "frontend/src/components/PlannerAI/**/*.jsx"
    ]
    
    for pattern in dirs_to_check:
        for filepath in glob.glob(pattern, recursive=True):
            if "node_modules" in filepath:
                continue
            try:
                if add_docstrings(filepath):
                    print(f"Added docstrings to {filepath}")
                    count += 1
            except Exception as e:
                print(f"Error processing {filepath}: {e}")
                
    print(f"Processed {count} frontend files.")
