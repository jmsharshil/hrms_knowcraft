import os
import json
import pdfplumber
import docx2txt
from pathlib import Path
from openai import AzureOpenAI
from pydantic import BaseModel
from django.conf import settings

client = AzureOpenAI(api_key=settings.OPENAI_API_KEY,azure_endpoint=settings.ENDPOINT_URL,api_version='2024-05-01-preview')

def extract_text(file_path):
    ext = Path(file_path).suffix.lower()

    if ext == ".pdf":
        with pdfplumber.open(file_path) as pdf:
            pages = [page.extract_text() or "" for page in pdf.pages]
            return "\n".join(pages)

    elif ext in [".doc", ".docx"]:
        return docx2txt.process(file_path)

    elif ext == ".txt":
        return Path(file_path).read_text()

    return ""

class Response(BaseModel):
    name: str
    phone_number: str
    email: str
    total_experience_years: int
    relevant_experience_years: int
    skills: list[str]  # <-- specify the type of items
    current_ctc: float
    expected_ctc: float
    education: list[str]  # also specify item type
    linkedin_url: str
    portfolio_url: str
    current_employer : str
    location :str

def parse_resume_ai(file_input):
    """
    Uses GPT-4o-mini to extract structured resume information.
    Returns a Python dict.
    """
    if hasattr(file_input, 'read'):
        import tempfile

        # create temp file with same extension
        suffix = Path(file_input.name).suffix or ".tmp"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            for chunk in file_input.chunks():
                tmp.write(chunk)
            temp_path = tmp.name
        file_path = temp_path
    else:
        file_path = file_input

    # Now safely extract text
    resume_text = extract_text(file_path)

    if 'temp_path' in locals():
        try:
            os.remove(temp_path)
        except:
            pass

    prompt = f"""
    You are an expert ATS resume parser.

    Extract the following fields from this resume:

    - name
    - email
    - phone_number
    - total_experience_years
    - relevant_experience_years
    - skills (list)
    - current_ctc (if exists)
    - expected_ctc (if exists)
    - education (list)
    - linkedin_url (if exists)
    - portfolio_url (if exists any other link)
    - current_employer : (if exists)
    - location (if exists)

    Resume:
    {resume_text}

    Return **VALID JSON ONLY**. No explanation. No comments.
    """

    res = client.chat.completions.parse(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
        # response_format= Response
        response_format={"type": "json_object"},
    )

    try:
        parsed = json.loads(res.choices[0].message.content)
    except Exception as e:
        print(e)
        parsed = {}

    return parsed


def calculate_match_score(parsed_resume, job):
    """
    Uses GPT-4o-mini to generate a 0–100 score.
    """

    prompt = f"""
    Evaluate how well the candidate fits the job. Score 0–100 ONLY.

    Candidate:
    {json.dumps(parsed_resume, indent=2)}

    Job:
    Title: {job.job_title}
    Required Skills: {job.skills_competencies}
    Experience Range: {job.experience_range}
    Key Responsibilities: {job.key_responsibility}
    Required Qualifications: {job.required_qualifications}

    Scoring Rules:
    - Skill match = 50%
    - Experience match = 30%
    - Role relevance = 20%

    Respond with ONLY the number score. No text.
    """

    res = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )

    try:
        return int(res.choices[0].message.content.strip())
    except Exception as e:
        print(e)
        return 0
