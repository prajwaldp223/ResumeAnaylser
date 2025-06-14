from flask import Flask, render_template, request, jsonify, send_file
from PyPDF2 import PdfReader
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from collections import Counter
import string
import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import spacy
from docx import Document
import os
import textwrap

app = Flask(__name__)

# Load English language model for NLP
try:
    nlp = spacy.load('en_core_web_sm')
except:
    os.system('python -m spacy download en_core_web_sm')
    nlp = spacy.load('en_core_web_sm')

def extract_text_from_pdf(pdf_file):
    pdf_reader = PdfReader(pdf_file)
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text()
    return text

def extract_keywords(text):
    # Tokenize and clean text
    doc = nlp(text.lower())
    
    # Remove stopwords, punctuation, and non-alphabetic tokens
    keywords = [token.text for token in doc if not token.is_stop and not token.is_punct and token.is_alpha]
    
    # Count occurrences of each keyword
    keyword_counts = Counter(keywords)
    
    return keyword_counts

def analyze_resume(job_description, resume_text):
    # Calculate similarity
    vectorizer = TfidfVectorizer(stop_words='english')
    vectors = vectorizer.fit_transform([job_description, resume_text])
    similarity = cosine_similarity(vectors)[0][1]
    match_percentage = round(similarity * 100, 2)
    
    # Extract personal details and sections
    personal_details = extract_personal_details(resume_text)
    sections = identify_sections(resume_text)
    entities = extract_entities(resume_text)
    
    # Extract keywords for skills analysis
    job_keywords = extract_keywords(job_description)
    resume_keywords = extract_keywords(resume_text)
    
    # Find missing keywords
    missing_keywords = []
    for word, count in job_keywords.items():
        if word not in resume_keywords or resume_keywords[word] < count:
            missing_keywords.append(word)
    
    # Get top keywords from job description
    top_job_keywords = [word for word, _ in job_keywords.most_common(10)]
    
    return {
        'match_percentage': match_percentage,
        'personal_details': personal_details,
        'sections': sections,
        'entities': entities,
        'missing_keywords': missing_keywords,
        'suggested_keywords': top_job_keywords
    }

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    job_description = request.form['job_description']
    resumes = request.files.getlist('resumes')
    
    results = []
    for resume in resumes:
        try:
            resume_text = extract_text_from_file(resume)
            analysis = analyze_resume(job_description, resume_text)
            results.append({
                'filename': resume.filename,
                'match_percentage': analysis['match_percentage'],
                'personal_details': analysis['personal_details'],
                'sections': analysis['sections'],
                'entities': analysis['entities'],
                'missing_keywords': analysis['missing_keywords'],
                'suggested_keywords': analysis['suggested_keywords']
            })
        except Exception as e:
            results.append({
                'filename': resume.filename,
                'error': str(e)
            })
    
    return jsonify(results)

if __name__ == '__main__':
    app.run(debug=True)