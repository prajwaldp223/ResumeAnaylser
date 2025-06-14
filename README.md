# Resume Analyzer

A powerful resume analysis tool that provides comprehensive insights and helps match resumes to job requirements.

## Features

### 1. Basic Resume Parsing
- Extract personal details (name, email, phone, LinkedIn/GitHub links)
- Identify sections (education, work experience, skills, projects, certifications)
- Extract entities using NLP (Named Entity Recognition)
- Parse multiple file types (PDF, DOCX, TXT)

### 2. Keyword Matching
- Match keywords from job description to resume
- Highlight missing or present keywords
- Provide match score for specific job roles

### 3. Skill Extraction & Categorization
- Classify skills (Technical, Soft, Tools, Languages, Frameworks)
- Show frequency or proficiency level
- Suggest missing in-demand skills

### 4. Experience & Education Analysis
- Calculate total work experience
- Highlight employment gaps
- Rank universities
- Identify role progression

### 5. Job Role Fit Analysis
- Resume vs. Job Requirements matching
- Qualification match
- Skills match
- Experience level match

### 6. ATS Compatibility Checker
- Check for ATS-friendly formatting
- Warn about formatting issues
- Provide improvement suggestions

### 7. Resume Grading
- Score based on structure
- Grammar and spelling check
- Keyword relevance
- Design and clarity

### 8. Customization Suggestions
- Tailor resume for specific roles
- Suggest action verbs
- Recommend content improvements

### 9. Multilingual Support
- Analyze resumes in different languages
- Translate sections as needed

### 10. Security & Privacy
- Mask sensitive data
- Secure file handling
- Data cleanup

### 11. Analytics Dashboard
- Batch resume analysis
- Filtering capabilities
- Visual summaries

### 12. Integration Features
- LinkedIn/GitHub integration
- Export capabilities
- HRMS integration

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/resume-analyzer.git
cd resume-analyzer
```

2. Create and activate a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Download required NLTK data:
```python
python -c "import nltk; nltk.download('punkt'); nltk.download('stopwords'); nltk.download('averaged_perceptron_tagger')"
```

5. Download spaCy model:
```bash
python -m spacy download en_core_web_sm
```

## Usage

1. Start the backend server:
```bash
python backend/app.py
```

2. Access the web interface at `http://localhost:5000`

3. Upload a resume and optionally provide a job description for matching

## API Endpoints

### Resume Analysis
- `POST /api/analyze`: Analyze a single resume
- `POST /api/batch-analyze`: Analyze multiple resumes
- `POST /api/suggest-improvements`: Get improvement suggestions
- `POST /api/translate`: Translate resume to another language

## Security

- JWT-based authentication
- Secure file handling
- Sensitive data masking
- Input validation
- XSS and SQL injection prevention

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- spaCy for NLP capabilities
- NLTK for text processing
- PyPDF2 for PDF handling
- python-docx for DOCX handling
- scikit-learn for machine learning features 