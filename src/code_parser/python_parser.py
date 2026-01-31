import ast

def analysis_python_file_structure(content: str) -> str:
    try:
        tree = ast.parse(content)
        nodes = []
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                nodes.append(node)
        
        # Sort by line number to provide a linear map
        nodes.sort(key=lambda x: x.lineno)
        
        output = []
        for node in nodes:
            type_name = "Class" if isinstance(node, ast.ClassDef) else "Function"
            # Indent methods if they are inside a class? 
            # For a simple map, flat list sorted by line number is a good start.
            output.append(f"Line {node.lineno}: {type_name} {node.name}")
            
        return "\n".join(output) if output else "No classes or functions found."

    except Exception as e:
        return f"Error parsing file structure: {str(e)}"