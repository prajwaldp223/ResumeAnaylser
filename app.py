from flask import Flask, render_template, request, jsonify
import PyPDF2
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from collections import Counter
import string

app = Flask(__name__)

def extract_text_from_pdf(pdf_file):
    pdf_reader = PyPDF2.PdfReader(pdf_file)
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text()
    return text

def extract_keywords(text):
    # Remove punctuation and convert to lowercase
    text = text.translate(str.maketrans('', '', string.punctuation)).lower()
    words = text.split()
    
    # Comprehensive list of common words to filter out
    stop_words = set([
        # Common articles, prepositions, and conjunctions
        'and', 'the', 'to', 'of', 'in', 'a', 'an', 'for', 'on', 'at', 'with', 'by',
        # Common verbs
        'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do',
        'does', 'did', 'will', 'would', 'shall', 'should', 'may', 'might', 'must', 'can',
        # Common descriptive words
        'such', 'as', 'like', 'so', 'very', 'more', 'most', 'other', 'some', 'many',
        # Common action words
        'using', 'utilize', 'utilized', 'performing', 'performed', 'conducting',
        'conducted', 'managing', 'managed',
        # Common skill-related phrases
        'ability', 'capable', 'proficient', 'experience', 'experienced', 'skill',
        'skilled', 'knowledge', 'understanding',
        # Common communication-related words
        'communication', 'oral', 'written', 'verbal', 'effectively', 'clearly',
        # Common problem-solving phrases
        'solving', 'solution', 'solutions', 'resolve', 'resolved', 'handling',
        'handled', 'managing', 'managed',
        # Common work-related words
        'work', 'working', 'worked', 'job', 'position', 'role', 'responsibility',
        'responsibilities', 'duty', 'duties'
    ])
    
    # Filter out common words
    keywords = [word for word in words if word not in stop_words]
    return Counter(keywords)

def analyze_resume(job_description, resume_text):
    # Calculate similarity
    vectorizer = TfidfVectorizer(stop_words='english')
    vectors = vectorizer.fit_transform([job_description, resume_text])
    similarity = cosine_similarity(vectors)[0][1]
    match_percentage = round(similarity * 100, 2)
    
    # Extract keywords
    job_keywords = extract_keywords(job_description)
    resume_keywords = extract_keywords(resume_text)
    
    # Find missing keywords (focusing on significant terms)
    missing_keywords = []
    for word, count in job_keywords.items():
        if len(word) > 2:  # Filter out very short words
            if word not in resume_keywords or resume_keywords[word] < count:
                missing_keywords.append(word)
    
    # Get top keywords from job description (excluding common words)
    top_job_keywords = [word for word, _ in job_keywords.most_common(15) 
                       if len(word) > 2]  # Filter out very short words
    
    return {
        'match_percentage': match_percentage,
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
        if resume.filename.endswith('.pdf'):
            resume_text = extract_text_from_pdf(resume)
            analysis = analyze_resume(job_description, resume_text)
            results.append({
                'filename': resume.filename,
                'match_percentage': analysis['match_percentage'],
                'missing_keywords': analysis['missing_keywords'],
                'suggested_keywords': analysis['suggested_keywords']
            })
    
    return jsonify(results)

if __name__ == '__main__':
    app.run(debug=True)