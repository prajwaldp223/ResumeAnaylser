from flask import Flask, render_template, request, jsonify
import PyPDF2
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

app = Flask(__name__)

def extract_text_from_pdf(pdf_file):
    pdf_reader = PyPDF2.PdfReader(pdf_file)
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text()
    return text

def calculate_similarity(job_description, resume_text):
    vectorizer = TfidfVectorizer()
    vectors = vectorizer.fit_transform([job_description, resume_text])
    similarity = cosine_similarity(vectors)[0][1]
    return round(similarity * 100, 2)

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
            match_percentage = calculate_similarity(job_description, resume_text)
            results.append({
                'filename': resume.filename,
                'match_percentage': match_percentage
            })
    
    return jsonify(results)

if __name__ == '__main__':
    app.run(debug=True)