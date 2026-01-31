from src.code_parser.python_parser import analysis_python_file_structure

def analysis_file_structure(content: str, file_path: str) -> str:
    file_extension = file_path.split(".")[-1]
    if file_extension == "py":
        return analysis_python_file_structure(content)
    else:
        return "Structure analysis currently only available for Python files."



    
