import re
import requests
from django.template.loader import render_to_string
from django.http import HttpResponse

def escape_latex(text):
    """
    Escapes characters that are special in LaTeX.
    """
    if not text:
        return ""
    
    # Cast to string and handle basic whitespace
    text = str(text)
    
    # Replacements dictionary for common LaTeX special characters
    replacements = {
        '\\': r'\textbackslash{}',
        '&': r'\&',
        '%': r'\%',
        '$': r'\$',
        '#': r'\#',
        '_': r'\_',
        '{': r'\{',
        '}': r'\}',
        '~': r'\textasciitilde{}',
        '^': r'\textasciicircum{}',
        '[': r'{[}',
        ']': r'{]}',
        '\n': r'\\ ',  # Basic line break support
    }
    
    # We use a specialized function to avoid double-escaping the backslashes we insert
    def replace(match):
        return replacements[match.group(0)]
    
    # Match patterns
    pattern = re.compile('|'.join(re.escape(k) for k in replacements.keys()))
    
    escaped = pattern.sub(replace, text)
    
    # Replace single quotes with balanced LaTeX quotes
    escaped = escaped.replace("'", "''").replace('"', "''")
    
    return escaped

def compile_latex_to_pdf(tex_content):
    """
    Compiles LaTeX to PDF via the public latexonline.cc API.
    Uses GET request as proven to work on this platform.
    Returns binary PDF data or raises Exception.
    """
    url = "https://latexonline.cc/compile"
    # Send the raw latex code as a query parameter
    response = requests.get(url, params={'text': tex_content})
    
    if response.status_code == 200 and response.headers.get('Content-Type') == 'application/pdf':
        return response.content
    else:
        error_msg = response.text[:500] if response.text else "Unknown error from latexonline"
        raise Exception(f"LaTeX Compilation Failed: {error_msg}")
