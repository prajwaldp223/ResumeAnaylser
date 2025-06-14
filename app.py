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

def extract_text_from_docx(docx_file):
    doc = Document(docx_file)
    text = ""
    for paragraph in doc.paragraphs:
        text += paragraph.text + '\n'
    return text

def extract_text_from_file(file):
    file_extension = file.filename.lower().split('.')[-1]
    if file_extension == 'pdf':
        return extract_text_from_pdf(file)
    elif file_extension == 'docx':
        return extract_text_from_docx(file)
    elif file_extension == 'txt':
        return file.read().decode('utf-8')
    else:
        raise ValueError(f'Unsupported file format: {file_extension}')

def extract_personal_details(text):
    # Process text with spaCy
    doc = nlp(text)
    
    # Initialize details dictionary
    details = {
        'name': '',
        'email': '',
        'phone': '',
        'links': []
    }
    
    # Extract email using regex
    email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    emails = re.findall(email_pattern, text)
    if emails:
        details['email'] = emails[0]
    
    # Extract phone numbers using regex
    phone_pattern = r'(?:\+\d{1,3}[- ]?)?\(?\d{3}\)?[- ]?\d{3}[- ]?\d{4}'
    phones = re.findall(phone_pattern, text)
    if phones:
        details['phone'] = phones[0]
    
    # Extract links (LinkedIn, GitHub)
    link_patterns = {
        'linkedin': r'linkedin\.com/\S+',
        'github': r'github\.com/\S+'
    }
    for platform, pattern in link_patterns.items():
        links = re.findall(pattern, text, re.IGNORECASE)
        if links:
            details['links'].extend(links)
    
    # Extract name using multiple strategies
    # Strategy 1: Check the first few lines of the resume (header)
    lines = text.split('\n')
    first_lines = [line.strip() for line in lines[:5] if line.strip()]
    
    # Look for a name in the first few lines
    name_found = False
    
    # First, try to find a name that's not an email or phone number
    for line in first_lines:
        # Skip if line contains email or phone patterns
        if re.search(email_pattern, line) or re.search(phone_pattern, line):
            continue
        
        # Skip if line contains common header words
        if re.search(r'resume|cv|curriculum\s+vitae', line, re.IGNORECASE):
            continue
            
        # Skip if line is too long to be a name
        if len(line) > 40:
            continue
            
        # Skip if line contains links
        if any(re.search(pattern, line, re.IGNORECASE) for _, pattern in link_patterns.items()):
            continue
        
        # If we get here, this line is likely a name
        details['name'] = line
        name_found = True
        break
    
    # Strategy 2: If no name found in header, try NER
    if not name_found:
        for ent in doc.ents:
            if ent.label_ == 'PERSON':
                details['name'] = ent.text
                break
    
    return details

def identify_sections(text):
    sections = {
        'education': [],
        'experience': [],
        'skills': [],
        'projects': [],
        'certifications': []
    }
    
    # Split text into lines
    lines = text.split('\n')
    current_section = None
    section_content = []
    
    # Common section headers
    section_headers = {
        'education': ['education', 'academic background', 'academic history'],
        'experience': ['experience', 'work experience', 'employment history', 'professional experience'],
        'skills': ['skills', 'technical skills', 'core competencies', 'expertise'],
        'projects': ['projects', 'personal projects', 'professional projects'],
        'certifications': ['certifications', 'certificates', 'professional certifications']
    }
    
    for line in lines:
        line = line.strip().lower()
        if not line:
            continue
        
        # Check if line is a section header
        found_section = None
        for section, headers in section_headers.items():
            if any(header in line for header in headers):
                found_section = section
                break
        
        if found_section:
            # Save previous section content
            if current_section and section_content:
                # Process section content into list items
                if current_section == 'skills':
                    # For skills, split by commas or semicolons
                    skills_text = ' '.join(section_content)
                    skills_list = [skill.strip() for skill in re.split(r'[,;]', skills_text) if skill.strip()]
                    sections[current_section] = skills_list
                else:
                    # For other sections, each line is a separate item
                    sections[current_section] = section_content
            # Start new section
            current_section = found_section
            section_content = []
        elif current_section:
            section_content.append(line)
    
    # Save last section content
    if current_section and section_content:
        # Process section content into list items
        if current_section == 'skills':
            # For skills, split by commas or semicolons
            skills_text = ' '.join(section_content)
            skills_list = [skill.strip() for skill in re.split(r'[,;]', skills_text) if skill.strip()]
            sections[current_section] = skills_list
        else:
            # For other sections, each line is a separate item
            sections[current_section] = section_content
    
    return sections

def extract_entities(text):
    doc = nlp(text)
    entities = {
        'organizations': [],
        'dates': [],
        'locations': [],
        'skills': [],
        'degrees': []
    }
    
    # Extract named entities
    for ent in doc.ents:
        if ent.label_ == 'ORG':
            entities['organizations'].append(ent.text)
        elif ent.label_ == 'DATE':
            entities['dates'].append(ent.text)
        elif ent.label_ == 'GPE':
            entities['locations'].append(ent.text)
    
    # Extract skills using custom patterns
    skill_patterns = ['python', 'java', 'javascript', 'html', 'css', 'sql', 'react', 'node.js',
                     'machine learning', 'data analysis', 'aws', 'docker', 'kubernetes']
    for pattern in skill_patterns:
        if pattern in text.lower():
            entities['skills'].append(pattern)
    
    # Extract degrees using patterns
    degree_patterns = ['bachelor', 'master', 'phd', 'b.tech', 'm.tech', 'b.e', 'm.e',
                      'b.sc', 'm.sc', 'bca', 'mca']
    for pattern in degree_patterns:
        if pattern in text.lower():
            entities['degrees'].append(pattern)
    
    return entities

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

@app.route('/optimize', methods=['POST'])
def optimize():
    job_description = request.form['job_description']
    resume = request.files['resume']
    
    try:
        # Extract text from the resume
        resume_text = extract_text_from_file(resume)
        
        # Analyze the resume
        analysis = analyze_resume(job_description, resume_text)
        
        # Create an optimized version of the resume
        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=letter)
        width, height = letter
        
        # Set font and sizes
        c.setFont("Helvetica-Bold", 16)
        
        # Handle name display - use name if found, otherwise leave blank
        name = analysis['personal_details'].get('name')
        if name and name.strip():
            c.drawString(72, height - 72, name)
        else:
            # If no name found, leave space for user to fill in
            c.drawString(72, height - 72, "[Your Name]")
        
        c.setFont("Helvetica", 10)
        y_position = height - 90
        
        # Add contact information
        if analysis['personal_details'].get('email'):
            c.drawString(72, y_position, f"Email: {analysis['personal_details']['email']}")
            y_position -= 15
        
        if analysis['personal_details'].get('phone'):
            c.drawString(72, y_position, f"Phone: {analysis['personal_details']['phone']}")
            y_position -= 15
        
        if analysis['personal_details'].get('links'):
            c.drawString(72, y_position, f"Links: {', '.join(analysis['personal_details']['links'])}")
            y_position -= 25
        
        # Add suggested keywords to skills section
        c.setFont("Helvetica-Bold", 12)
        c.drawString(72, y_position, "Skills")
        y_position -= 20
        
        c.setFont("Helvetica", 10)
        skills = set(analysis['sections'].get('skills', []))
        
        # Add suggested keywords to skills
        for keyword in analysis['suggested_keywords']:
            skills.add(keyword)
        
        skills_text = ", ".join(skills)
        
        # Wrap text for skills
        wrapped_skills = textwrap.wrap(skills_text, width=80)
        for line in wrapped_skills:
            c.drawString(72, y_position, line)
            y_position -= 15
        
        y_position -= 15
        
        # Add education section
        if analysis['sections'].get('education'):
            c.setFont("Helvetica-Bold", 12)
            c.drawString(72, y_position, "Education")
            y_position -= 20
            
            c.setFont("Helvetica", 10)
            for edu in analysis['sections']['education']:
                wrapped_edu = textwrap.wrap(edu, width=80)
                for line in wrapped_edu:
                    c.drawString(72, y_position, line)
                    y_position -= 15
                y_position -= 5
        
        # Add experience section
        if analysis['sections'].get('experience'):
            c.setFont("Helvetica-Bold", 12)
            c.drawString(72, y_position, "Work Experience")
            y_position -= 20
            
            c.setFont("Helvetica", 10)
            for exp in analysis['sections']['experience']:
                wrapped_exp = textwrap.wrap(exp, width=80)
                for line in wrapped_exp:
                    c.drawString(72, y_position, line)
                    y_position -= 15
                y_position -= 5
        
        # Add projects section
        if analysis['sections'].get('projects'):
            c.setFont("Helvetica-Bold", 12)
            c.drawString(72, y_position, "Projects")
            y_position -= 20
            
            c.setFont("Helvetica", 10)
            for proj in analysis['sections']['projects']:
                wrapped_proj = textwrap.wrap(proj, width=80)
                for line in wrapped_proj:
                    c.drawString(72, y_position, line)
                    y_position -= 15
                y_position -= 5
        
        # Add certifications section
        if analysis['sections'].get('certifications'):
            c.setFont("Helvetica-Bold", 12)
            c.drawString(72, y_position, "Certifications")
            y_position -= 20
            
            c.setFont("Helvetica", 10)
            for cert in analysis['sections']['certifications']:
                wrapped_cert = textwrap.wrap(cert, width=80)
                for line in wrapped_cert:
                    c.drawString(72, y_position, line)
                    y_position -= 15
                y_position -= 5
        
        c.save()
        buffer.seek(0)
        
        return send_file(
            buffer,
            as_attachment=True,
            download_name=f"optimized_{resume.filename.rsplit('.', 1)[0]}.pdf",
            mimetype='application/pdf'
        )
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)