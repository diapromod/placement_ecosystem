import re
import requests
from django.template.loader import render_to_string
from django.http import HttpResponse

def escape_latex(text):
    """
    Escapes characters that are special in LaTeX:
    & % $ # _ { } ~ ^ \
    """
    if not text:
        return ""
    # simple replacements
    replacements = {
        '&': r'\&',
        '%': r'\%',
        '$': r'\$',
        '#': r'\#',
        '_': r'\_',
        '{': r'\{',
        '}': r'\}',
        '~': r'\textasciitilde{}',
        '^': r'\textasciicircum{}',
        '\\': r'\textbackslash{}',
    }
    # Create a regex to match any of the keys in replacements
    regex = re.compile('|'.join(re.escape(str(key)) for key in replacements.keys()))
    return regex.sub(lambda match: replacements[match.group(0)], str(text))

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
