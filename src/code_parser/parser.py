from src.code_parser.tree_sitter_parser import UniversalParser

# Extension to Tree-sitter language name mapping
EXT_TO_LANG = {
    "py": "python",
    "js": "javascript",
    "jsx": "javascript",
    "ts": "typescript",
    "tsx": "typescript",
    "go": "go",
    "java": "java",
    "cpp": "cpp",
    "c": "c",
    "rb": "ruby",
    "rs": "rust",
}

def analysis_file_structure(content: str, file_path: str) -> str:
    file_extension = file_path.split(".")[-1].lower()
    
    if file_extension in EXT_TO_LANG:
        lang_name = EXT_TO_LANG[file_extension]
        parser = UniversalParser()
        return parser.parse_structure(content, lang_name)
    else:
        return f"Structure analysis currently only available for: {', '.join(EXT_TO_LANG.keys())}"

def get_function_content(content: str, file_path: str, target_name: str) -> str:
    file_extension = file_path.split(".")[-1].lower()
    
    if file_extension in EXT_TO_LANG:
        lang_name = EXT_TO_LANG[file_extension]
        parser = UniversalParser()
        return parser.extract_function_content(content, lang_name, target_name)
    else:
        return f"Function extraction currently only available for: {', '.join(EXT_TO_LANG.keys())}"




    
