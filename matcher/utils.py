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
    
    return None

def extract_job_title(text):
    """
    Heuristic to extract Job Title / Company from JD text.
    Looks at the first few lines of the text.
    """
    if not text:
        return None
        
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not lines:
        return None
        
    # Heuristic: The first or second line often contains the title or company.
    # We look for lines that aren't too long and contain letter characters.
    for i in range(min(3, len(lines))):
        line = lines[i]
        # Ignore lines that look like generic headers (e.g., "JOB DESCRIPTION")
        if line.lower() in ["job description", "jd", "position", "role"]:
            continue
        if 5 < len(line) < 100:
            return line
            
    return None

def extract_cgpa(text):
    """
    Extract CGPA from resume text.
    Looks for patterns like:
    - CGPA: 8.5
    - GPA 3.8/4.0
    - 8.5 CGPA
    - CGPA 8.5 out of 10
    """
    if not text:
        return None
    
    # Normalize text
    text_lower = text.lower()
    
    # Pattern 1: "CGPA: 8.5" or "GPA: 3.8"
    match = re.search(r'(?:cgpa|gpa)\s*:?\s*(\d+\.?\d*)', text_lower)
    if match:
        cgpa = float(match.group(1))
        # Normalize to 10-point scale if needed
        if cgpa <= 4.0:  # Likely 4.0 scale
            cgpa = (cgpa / 4.0) * 10.0
        return round(cgpa, 2)
    
    # Pattern 2: "8.5 CGPA" or "8.5/10"
    match = re.search(r'(\d+\.?\d*)\s*(?:cgpa|gpa|/10)', text_lower)
    if match:
        cgpa = float(match.group(1))
        if cgpa <= 4.0:
            cgpa = (cgpa / 4.0) * 10.0
        return round(cgpa, 2)
    
    return None

def extract_department(text):
    """
    Extract department/branch from resume.
    Looks for common engineering departments.
    """
    if not text:
        return None
    
    # Common department keywords
    departments = {
        'computer science': ['computer science', 'cs', 'cse', 'computer engineering'],
        'information technology': ['information technology', 'it', 'info tech'],
        'electronics': ['electronics', 'ece', 'electronics and communication', 'electronics & communication'],
        'electrical': ['electrical', 'ee', 'electrical engineering'],
        'mechanical': ['mechanical', 'me', 'mechanical engineering'],
        'civil': ['civil', 'ce', 'civil engineering'],
        'chemical': ['chemical', 'che', 'chemical engineering'],
        'biotechnology': ['biotechnology', 'biotech', 'bt'],
        'data science': ['data science', 'ds', 'data analytics'],
    }
    
    text_lower = text.lower()
    
    # Look for department mentions
    for dept_name, keywords in departments.items():
        for keyword in keywords:
            # Use word boundaries to avoid partial matches
            pattern = r'\b' + re.escape(keyword) + r'\b'
            if re.search(pattern, text_lower):
                return dept_name.title()
    
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
# ---------- SBERT Semantic Utilities ----------
def sbert_similarity_score(text_a, text_b):
    """Compute cosine similarity between two strings."""
    if not SBERT_AVAILABLE or not text_a or not text_b:
        return 0.0
    emb_a = SBERT_MODEL.encode(text_a, convert_to_tensor=True)
    emb_b = SBERT_MODEL.encode(text_b, convert_to_tensor=True)
    return util.cos_sim(emb_a, emb_b).item()

def get_semantic_matches(candidate_skills, required_skills, threshold=0.75):
    """
    Finds which required skills are 'matched' semantically by candidate skills.
    Returns:
        - semantic_matches: List of tuples (required_skill, candidate_skill, score)
        - semantic_matched_set: Set of required skills found semantically
    """
    if not SBERT_AVAILABLE or not candidate_skills or not required_skills:
        return [], set()

    # Encode all candidate skills once
    cand_embs = SBERT_MODEL.encode(candidate_skills, convert_to_tensor=True)
    
    matches = []
    matched_set = set()
    
    for req in required_skills:
        req_emb = SBERT_MODEL.encode(req, convert_to_tensor=True)
        # Compute similarity against all candidate skills
        scores = util.cos_sim(req_emb, cand_embs)[0]
        max_score, idx = scores.max().item(), scores.argmax().item()
        
        if max_score >= threshold:
            matches.append((req, candidate_skills[idx], round(max_score, 2)))
            matched_set.add(req)
            
    return matches, matched_set

# ---------- Unified Matching Analysis ----------
def analyze_match(resume_text, jd_text, resume_skills, jd_skills):
    """
    Unified matching analysis using Keyword and Precise Semantic analysis.
    """
    resume_skills_set = set(resume_skills or [])
    jd_skills_set = set(jd_skills or [])
    
    # 1. Direct Keyword Match
    matched = resume_skills_set.intersection(jd_skills_set)
    potentially_missing = jd_skills_set - resume_skills_set
    
    # 2. Semantic Analysis (Handling Synonyms)
    semantic_insights = []
    semantic_matched_reqs = set()
    
    if SBERT_AVAILABLE and potentially_missing and resume_skills:
        semantic_insights, semantic_matched_reqs = get_semantic_matches(
            list(resume_skills_set), 
            list(potentially_missing)
        )
    
    # Actual missing (not found by keyword OR semantic match)
    missing = potentially_missing - semantic_matched_reqs
    
    # 3. Normalized Scoring
    # Total Score = (Exact Keyword Matches + Semantic Partial Matches) / Total Requirements
    total_reqs = len(jd_skills_set)
    if total_reqs > 0:
        # We value exact matches at 1.0 and semantic matches at 0.85
        score_val = (len(matched) * 1.0) + (len(semantic_matched_reqs) * 0.85)
        final_score = (score_val / total_reqs) * 100
    else:
        final_score = 0.0

    # 4. Content-based Semantic Score (Full text context)
    full_text_sim = 0.0
    if SBERT_AVAILABLE and resume_text and jd_text:
        full_text_sim = sbert_similarity_score(resume_text, jd_text) * 100

    # Adjust final score slightly based on full-text context (±5%)
    # This rewards resumes that have the right 'tone' and 'context'
    if full_text_sim > 0:
        context_bonus = (full_text_sim - 50) / 10 # -5 to +5 range
        final_score = max(0, min(100, final_score + context_bonus))

    # 5. Generate Summary
    if final_score >= 75:
        summary = "Excellent match! You meet most technical requirements."
    elif final_score >= 50:
        summary = "Good match. Your profile is relevant, but some core skills are missing."
    elif final_score >= 25:
        summary = "Partial match. You have some related skills, but clear gaps exist."
    else:
        summary = "Low match. The technology stack doesn't align well with your profile."
    
    return {
        'score': round(final_score, 1),
        'matched_skills': sorted(matched),
        'semantic_matches': semantic_insights, # List of (req_skill, has_skill, score)
        'missing_skills': sorted(missing),
        'summary': summary,
        'keyword_match_count': len(matched),
        'semantic_match_count': len(semantic_matched_reqs),
        'full_text_sim': round(full_text_sim, 1) if full_text_sim > 0 else None,
    }


