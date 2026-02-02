import re
from pathlib import Path
from io import BytesIO

import pdfplumber
from docx import Document

# Optional SBERT import (only if you installed sentence-transformers)
try:
    from sentence_transformers import SentenceTransformer, util
    SBERT_AVAILABLE = True
    SBERT_MODEL = SentenceTransformer("all-MiniLM-L6-v2")  # small, fast
except Exception:
    SBERT_AVAILABLE = False
    SBERT_MODEL = None

# Simple skill dictionary (expandable)
SKILL_LIST = [
    "python", "java", "c++", "c", "django", "flask", "sql", "mongodb", "react",
    "javascript", "html", "css", "aws", "azure", "docker", "kubernetes",
    "machine learning", "deep learning", "pandas", "numpy", "tensorflow",
    "pytorch", "git", "linux"
]

# ---------- File text extraction ----------
def extract_text_from_pdf_fileobj(file_obj):
    """
    Accepts a file-like object (InMemoryUploadedFile or opened file) for PDF.
    Returns text (string).
    """
    text_pages = []
    try:
        with pdfplumber.open(file_obj) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text_pages.append(page_text)
    except Exception:
        # fallback: return empty
        return ""
    return "\n".join(text_pages)


def extract_text_from_docx_fileobj(file_obj):
    """
    Accepts a file-like object for DOCX.
    Returns text (string).
    """
    doc = Document(file_obj)
    paras = [p.text for p in doc.paragraphs if p.text]
    return "\n".join(paras)


def extract_text_from_file(uploaded_file):
    """
    Generic: checks file extension and routes to relevant extractor.
    uploaded_file can be Django InMemoryUploadedFile or path.
    """
    name = getattr(uploaded_file, "name", "")
    lower = name.lower()
    if lower.endswith(".pdf"):
        # pdfplumber can accept file-like object
        return extract_text_from_pdf_fileobj(uploaded_file)
    elif lower.endswith(".docx"):
        return extract_text_from_docx_fileobj(uploaded_file)
    elif lower.endswith(".txt"):
        return uploaded_file.read().decode(errors="ignore")
    else:
        # try pdf as fallback
        try:
            return extract_text_from_pdf_fileobj(uploaded_file)
        except Exception:
            return ""


# Optional spaCy import for robust name extraction
try:
    import spacy
    try:
        NLP = spacy.load("en_core_web_sm")
    except OSError:
        NLP = None
except ImportError:
    NLP = None

# ---------- Lightweight extraction helpers ----------
_email_re = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
_phone_re = re.compile(r"(\+?\d{1,3}[-\s]?)?(\d{10}|\d{5}[-\s]?\d{5})")

def extract_email(text):
    m = _email_re.search(text)
    return m.group(0) if m else None

def extract_phone(text):
    m = _phone_re.search(text)
    if not m:
        return None
    return m.group(0)

def extract_name(text):
    """
    Robust name extraction using spaCy NER with heuristic fallback.
    1. Try spaCy to identify PERSON entities
    2. Fall back to first-line heuristic if spaCy unavailable
    """
    if not text:
        return None
    
    # Try spaCy NER first
    if NLP:
        doc = NLP(text[:1000])  # Limit to first 1000 chars for performance
        for ent in doc.ents:
            if ent.label_ == "PERSON":
                name = ent.text.strip()
                # Filter out obvious false positives
                if (len(name.split()) >= 2 and 
                    "resume" not in name.lower() and
                    len(name) < 50):  # Reasonable name length
                    return name
    
    # Fallback: heuristic (first non-empty line with 2-4 words)
    for line in text.splitlines():
        s = line.strip()
        if not s:
            continue
        if re.search(r"[A-Za-z]", s) and 2 <= len(s.split()) <= 4:
            return s
    return None

# ---------- Skills extraction ----------
def normalize_text(t: str):
    return re.sub(r"[^\w\s]", " ", t).lower()

def extract_skills_from_text(text, skill_set=SKILL_LIST):
    """Return list of matched skills (normalized)"""
    if not text:
        return []
    norm = normalize_text(text)
    found = set()
    for s in skill_set:
        if s.lower() in norm:
            found.add(s.lower())
    return sorted(found)

# ---------- JD parsing (simple) ----------
def parse_jd_for_skills(jd_text):
    # reuse same skill list
    return extract_skills_from_text(jd_text)

# ---------- Matching & scoring ----------
def jaccard_score(set_a, set_b):
    a = set(set_a)
    b = set(set_b)
    if not a and not b:
        return 1.0
    if not a or not b:
        return 0.0
    inter = a.intersection(b)
    union = a.union(b)
    return len(inter) / len(union)

def heuristic_weighted_score(resume_skills, jd_skills, weights=None):
    """
    Very simple scoring:
    - skill match proportion weighted with skill weight
    - (we keep only skills for now; you can add education/exp later)
    `weights` is dict with keys 'skills','education','experience' etc
    """
    if weights is None:
        weights = {"skills": 1.0}

    skill_score = 0.0
    if jd_skills:
        matched = set(resume_skills).intersection(set(jd_skills))
        skill_score = len(matched) / max(1, len(set(jd_skills)))
    total = skill_score * weights.get("skills", 1.0)
    return round(total, 4)

# ---------- Optional SBERT semantic similarity ----------
def sbert_similarity_score(resume_text, jd_text):
    """
    If SBERT installed, compute semantic similarity between the full texts.
    Returns cosine similarity float [0,1]
    """
    if not SBERT_AVAILABLE:
        raise RuntimeError("SBERT not available; install sentence-transformers.")
    # encode
    emb_r = SBERT_MODEL.encode(resume_text, convert_to_tensor=True)
    emb_j = SBERT_MODEL.encode(jd_text, convert_to_tensor=True)
    sim = util.cos_sim(emb_r, emb_j).item()
    # numeric -> clamp 0..1
    return max(0.0, min(1.0, float(sim)))
