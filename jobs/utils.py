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
    location : str
    experience : list[str]

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
    - experience (list)
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
    Technical Skills: {job.technical_skills}
    Experience Range: {job.experience_range}
    Key Responsibilities: {job.key_responsibility}
    Required Qualifications: {job.required_qualifications}

    Scoring Rules:
    - Skill match = 50%
    - Experience match = 30%
    - Role relevance = 20%

    Respond with ONLY the number score and reason. No extra text.Return **VALID JSON ONLY**
    """

    res = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
        response_format={"type": "json_object"},
    )

    try:
        return json.loads(res.choices[0].message.content.strip())
    except Exception as e:
        print(e)
        return 0

from string import Template
from html import escape
HTML_TEMPLATE = Template(r"""
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8"/>
<title>Resume Fit Report</title>

<style>
body {
    margin: 0;
    padding: 30px;
    background: #f4f6fb;
    font-family: "Inter", Arial, sans-serif;
    color: #1f2430;
}
.card {
    max-width: 900px;
    margin: auto;
    background: #ffffff;
    border-radius: 16px;
    padding: 32px;
    box-shadow: 0 12px 40px rgba(0,0,0,0.08);
    border: 1px solid #e6ebf5;
}
.header {
    text-align: center;
    margin-bottom: 22px;
}
.header h1 {
    margin: 6px 0 2px 0;
    font-size: 28px;
    font-weight: 700;
}
.header h2 {
    margin: 0;
    font-size: 16px;
    color: #6c7a92;
    font-weight: 500;
}

/* Section Title */
.section-title {
    font-size: 18px;
    font-weight: 700;
    margin-top: 30px;
    margin-bottom: 10px;
    padding-left: 12px;
    border-left: 4px solid #4c79ff;
}

/* Panels */
.panel {
    background: #fafcff;
    border: 1px solid #e7edfa;
    padding: 18px;
    border-radius: 12px;
    font-size: 15px;
    line-height: 1.55;
}

/* Lists */
ul.clean {
    margin: 0;
    padding-left: 22px;
}
ul.clean li {
    margin-bottom: 6px;
}

/* Skill Chips */
.skill-chip {
    display: inline-block;
    padding: 6px 12px;
    border-radius: 20px;
    background: #eef3ff;
    border: 1px solid #d8e3ff;
    margin: 4px 6px 4px 0;
    font-size: 13px;
}

/* SVG PIE CHART */
.pie-wrapper {
    text-align: center;
    margin: 26px 0;
}
svg.pie {
    width: 180px;
    height: 180px;
}
.pie text {
    font-size: 28px;
    fill: #1a2234;
    font-weight: 700;
}
</style>
</head>

<body>
<div class="card">

    <!-- Header -->
    <div class="header">
        <h1>$candidate_name</h1>
        <h2>$job_title</h2>
    </div>

    <!-- SVG Pie Chart -->
    <div class="pie-wrapper">
        <svg class="pie" viewBox="0 0 36 36">
            <path
                d="M18 2.0845
                   a 15.9155 15.9155 0 0 1 0 31.831
                   a 15.9155 15.9155 0 0 1 0 -31.831"
                fill="none"
                stroke="#e9eef7"
                stroke-width="3.8"
            />
            <path
                d="M18 2.0845
                   a 15.9155 15.9155 0 0 1 0 31.831"
                fill="none"
                stroke="#4c79ff"
                stroke-width="3.8"
                stroke-dasharray="$score, 100"
            />
            <text x="18" y="20.5" text-anchor="middle">$score%</text>
        </svg>
    </div>

    <!-- Contact -->
    <div class="section-title">Contact</div>
    <div class="panel">
        <strong>Email:</strong> $candidate_email<br/>
        <strong>Phone:</strong> $candidate_phone<br/>
        <strong>LinkedIn:</strong> $linkedin_url
    </div>

    <!-- Skills -->
    <div class="section-title">Skills</div>
    <div class="panel">
        $skills_html
    </div>

    <!-- Education -->
    <div class="section-title">Education</div>
    <div class="panel">
        <ul class="clean">
            $education_html
        </ul>
    </div>

    <!-- Projects -->
    <div class="section-title">Projects</div>
    <div class="panel">
        <ul class="clean">
            $projects_html
        </ul>
    </div>

    <!-- Work Experience -->
    <div class="section-title">Work Experience</div>
    <div class="panel">
        <ul class="clean">
            $experience_html
        </ul>
    </div>

    <!-- Achievements -->
    <div class="section-title">Achievements</div>
    <div class="panel">
        <ul class="clean">
            $achievements_html
        </ul>
    </div>

</div>
</body>
</html>
""")
from html import escape

def format_contact(email, phone, linkedin):
    return f"""
    <p class="contact-item"><b>Email:</b> {email or "<span class='empty'>Not provided</span>"}</p>
    <p class="contact-item"><b>Phone:</b> {phone or "<span class='empty'>Not provided</span>"}</p>
    <p class="contact-item"><b>LinkedIn:</b> {linkedin or "<span class='empty'>Not provided</span>"}</p>
    """

def format_skills_tags(skills):
    if not skills:
        return "<span class='empty'>No skills provided</span>"

    return "<ul class='skills-list'>" + "".join(
        f"<li class='skill-item'>{escape(str(skill))}</li>" for skill in skills
    ) + "</ul>"

def format_education_right(items):
    if not items:
        return "<p><span class='empty'>No education provided</span></p>"

    html = ""
    for ed in items:
        if isinstance(ed, dict):
            degree = escape(ed.get("degree", ""))
            field = escape(ed.get("field", ""))
            inst = escape(ed.get("institution", ""))
            duration = escape(ed.get("duration", ""))
            html += f"""
            <p>
              <b>{degree}{f" in {field}" if field else ""}</b><br>
              {inst} ({duration})
            </p>
            """
        else:
            html += f"<p>{escape(str(ed))}</p>"
    return html

def format_experience_right(items):
    if not items:
        return "<p><span class='empty'>No experience provided</span></p>"

    html = ""
    for ex in items:
        if isinstance(ex, dict):
            title = escape(ex.get("title", ""))
            emp = escape(ex.get("employer", ""))
            duration = escape(ex.get("duration", ""))
            html += f"""
            <p>
              <b>{title}</b> – {emp}<br>
              <span class="duration">{duration}</span>
            </p>
            """
        else:
            html += f"<p>{escape(str(ex))}</p>"
    return html

def format_reason(reason):
    return escape(reason) if reason else "<span class='empty'>No reason provided</span>"

def render_beautiful_report(parsed, job, overall_score):
    from html import escape

    name = escape(parsed.get("name", ""))
    email = escape(parsed.get("email") or parsed.get("candidate_email") or "")
    phone = escape(parsed.get("phone") or parsed.get("phone_number") or "")
    linkedin = escape(parsed.get("linkedin_url") or "")
    job_title = escape(
        getattr(job, "job_title", "") or
        (job.get("job_title") if isinstance(job, dict) else "")
    )

    score = max(0, min(100, int(overall_score or 0)))
    reason = format_reason(parsed.get("reason"))
    skills = parsed.get("skills", [])
    education = parsed.get("education", [])
    experience = parsed.get("experience", [])
    projects = parsed.get("projects", [])
    achievements = parsed.get("achievements", [])
    html = f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  body {{
    font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
    background: #ffffff;
    color: #333333;
    padding: 20px;
    font-size: 14px;
    line-height: 1.5;
  }}
  .container {{
    max-width: 1200px;
    margin: 0 auto;
    background: #ffffff;
  }}
  .header {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
  }}
  .logo {{
    font-size: 24px;
    font-weight: bold;
    color: #007bff;
  }}
  .website {{
    font-size: 12px;
    color: #007bff;
  }}
  .name-title {{
    text-align: center;
    margin-bottom: 30px;
  }}
  .name {{
    font-size: 28px;
    font-weight: bold;
    color: #2c3e50;
    margin: 0;
  }}
  .title {{
    font-size: 18px;
    color: #7f8c8d;
    margin-top: 5px;
  }}
  .main-content {{
    display: flex;
    justify-content: space-between;
    gap: 20px;
  }}
  .left-column {{
    flex: 1;
  }}
  .middle-column {{
    flex: 1;
    text-align: center;
  }}
  .right-column {{
    flex: 1;
  }}
  .section-title {{
    font-size: 18px;
    font-weight: 600;
    color: #34495e;
    margin-bottom: 10px;
  }}
  .skills-matching {{
    display: flex;
    align-items: center;
    margin-bottom: 20px;
  }}
  .circle {{
    width: 80px;
    height: 80px;
    border-radius: 50%;
    background: conic-gradient(#e74c3c 0% 20%, #ecf0f1 20% 100%);
    display: flex;
    align-items: center;
    justify-content: center;
    color: #ffffff;
    font-size: 24px;
    font-weight: bold;
    margin-right: 15px;
  }}
  .reason-fit {{
    font-size: 13px;
    color: #555555;
  }}
  .skills-category {{
    background: #3498db;
    color: #ffffff;
    padding: 5px 10px;
    border-radius: 4px;
    margin-bottom: 10px;
    font-weight: bold;
  }}
  .skills-list {{
    list-style-type: none;
    padding: 0;
    display: flex;
    flex-wrap: wrap;
    gap: 5px;
  }}
  .skill-item {{
    background: #3498db;
    color: #ffffff;
    padding: 5px 10px;
    border-radius: 4px;
    font-size: 12px;
  }}
  .illustration {{
    max-width: 200px;
    margin: 20px auto;
  }}
  .behavioral-traits {{
    list-style-type: none;
    padding: 0;
  }}
  .trait-item {{
    font-size: 14px;
    margin-bottom: 10px;
    color: #2980b9;
  }}
  .tenure {{
    display: flex;
    justify-content: space-around;
    margin: 20px 0;
  }}
  .tenure-item {{
    text-align: center;
  }}
  .tenure-circle {{
    width: 60px;
    height: 60px;
    border-radius: 50%;
    background: #8e44ad;
    color: #ffffff;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 18px;
    font-weight: bold;
    margin: 0 auto 5px;
  }}
  .tenure-desc {{
    font-size: 12px;
    color: #555555;
  }}
  .projects-list {{
    list-style-type: none;
    padding: 0;
  }}
  .project-item {{
    margin-bottom: 15px;
  }}
  .project-title {{
    font-weight: bold;
  }}
  .project-industry {{
    font-style: italic;
    color: #7f8c8d;
  }}
  .achievements {{
    margin-top: 20px;
  }}
  .questions-section {{
    margin-top: 40px;
    display: flex;
    justify-content: space-between;
    gap: 20px;
  }}
  .questions-column {{
    flex: 1;
  }}
  .questions-list {{
    list-style-type: disc;
    padding-left: 20px;
  }}
  .task {{
    margin-top: 20px;
    font-style: italic;
  }}
  .contact {{
    margin-bottom: 20px;
  }}
  .contact-item {{
    margin-bottom: 5px;
  }}
</style>
</head>
<body>

<div class="container">

  <div class="header">
    <div class="logo">KA</div>
    <div class="website">https://www.knowcraftanalytics.com/</div>
  </div>

  <div class="name-title">
    <h1 class="name">{name}</h1>
    <p class="title">{job_title}</p>
  </div>

  <div class="main-content">

    <!-- LEFT COLUMN -->
    <div class="left-column">

      <div class="contact">
        <div class="section-title">Contact Information</div>
        {format_contact(email, phone, linkedin)}
      </div>

      <div class="section-title">Skills Matching</div>
      <div class="skills-matching">
        <div class="circle">{score}%</div>
        <div class="reason-fit">{reason}</div>
      </div>

      <div class="section-title">Skills</div>
      {format_skills_tags(skills)}

    </div>

    <!-- MIDDLE COLUMN -->
    <div class="middle-column">

      <img class="illustration"
        src="https://thumbs.dreamstime.com/b/young-smiling-man-james-working-laptop-writing-code-create-software-engineering-web-development-programming-coding-concept-403198904.jpg">

      <div class="section-title">Profile Summary</div>
      <p>🎯 Role: {job_title}</p>
      <p>🎓 Education: {escape(education[0]) if education else "Not provided"}</p>

    </div>

    <!-- RIGHT COLUMN -->
    <div class="right-column">

      <div class="section-title">Projects</div>
      {format_skills_tags(projects)}

      <div class="section-title">Education</div>
      {format_education_right(education)}

      <div class="section-title">Experience</div>
      {format_experience_right(experience)}

    </div>

  </div>

  <div class="achievements">
    <div class="section-title">Achievements</div>
    {format_skills_tags(achievements)}
  </div>

</div>
</body>
</html>
"""
    return html

def create_resume_report_html(parsed_resume, job):
    """
    Uses GPT-4o-mini to generate resume report in HTML format.
    """

    prompt = f"""
    Create a professional resume–job-fit report in **pure HTML**.

    Include these sections clearly with headings and clean formatting:
    - Candidate Name
    - Job Title
    - Skill Match (%)  
    - Reason for Match / Mismatch
    - Skills
    - Education
    - Projects (if any)
    - Tenure History (if any)
    - Achievements (if any)

    Candidate Parsed Data (JSON):
    {json.dumps(parsed_resume, indent=2)}

    Job Details:
    Title: {job.job_title}
    Required Skills: {job.skills_competencies}
    Experience Range: {job.experience_range}
    Key Responsibilities: {job.key_responsibility}
    Required Qualifications: {job.required_qualifications}

    Scoring rule:
    - Skill match = 50%
    - Experience match = 30%
    - Role relevance = 20%

    Output must be **HTML**, including:
    - <h1>, <h2>, <p>, <ul>, <li>, <table> etc.
    - No scripts
    - No external CSS (You can use inline css or in <style> tag to make it stylish and more professional)
    Use this template for reference for style: {HTML_TEMPLATE}
    Don't add even a single extra word after the HTML template
    """

    res = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
    )

    return res.choices[0].message.content.strip()

from django.db import transaction
from .models import JobApplication
from django.utils import timezone
from datetime import timedelta

def parse_resume_task(application,resume_file,job):
    # ---- AI extraction ----
    parsed = parse_resume_ai(resume_file)
    name = parsed.get('name') or parsed.get('full_name')
    email = parsed.get('email')
    phone = parsed.get('phone_number') or parsed.get('phone')
    phone = phone.replace(" ",'')
    total_experience_years = parsed.get("total_experience_years")
    relevant_experience_years = parsed.get("relevant_experience_years")
    skills = parsed.get('skills')
    education = parsed.get("education")
    current_ctc = parsed.get("current_ctc")
    expected_ctc = parsed.get("expected_ctc",'')
    linkedin_url = parsed.get("linkedin_url",'')
    portfolio_url = parsed.get("portfolio_url",'')
    location = parsed.get("location")
    current_employer = parsed.get("current_employer")
    history = []
    if email:
        today = timezone.now()
        six_months_ago = today - timedelta(days=6*30)
        duplicate_application = JobApplication.objects.filter(candidate_email=email,created_at__gte=six_months_ago).exclude(id=application.id)
        duplicated = False
        if duplicate_application.exists():
            print("Duplicate resume found!")
            history = build_candidate_history(email,application.id)
            duplicated = True
    # ---- AI scoring ----
    ai_match = calculate_match_score(parsed, job)
    ai_score = int(ai_match.get('score'))
    match_reason = ai_match.get('reason')
    parsed['match_reason'] = match_reason
    # ---- AI Report ----
    # html_report = create_resume_report_html(parsed,link.job)
    html_report = render_beautiful_report(parsed,job,ai_score)
    from onboarding.utils.pdf_maker import html_to_pdf
    report_pdf = html_to_pdf(html_report)
    from django.core.files.base import ContentFile
    pdf_file = ContentFile(report_pdf, name=f"{name}_{email}_resume_report.pdf")
    with transaction.atomic():
        application.candidate_name = name
        application.candidate_email = email
        application.candidate_phone = phone
        application.relevant_experience_years = relevant_experience_years
        application.experience_years = total_experience_years
        application.linkedin_url = linkedin_url
        application.current_ctc = current_ctc
        application.expected_ctc = expected_ctc
        application.portfolio_url = portfolio_url
        application.skill = skills
        application.education = education
        application.current_employer = current_employer
        application.location = location
        application.match_score = ai_score
        application.resume_report.save(f"{name}_{email}_resume_report.pdf", pdf_file, save=True)
        application.is_duplicate = duplicated
        application.candidate_history = history
        application.save()
    
    if application.is_duplicate:
        from onboarding.utils.engine import automation_engine
        
        automation_engine(application,application.status,'duplicate_rejected')
    if application.match_score >= 75:
        automation_engine(application,application.status,'shortlisted')

def build_candidate_history(email, exclude_application_id=None):
    qs = JobApplication.objects.filter(
        candidate_email=email
    ).order_by("-created_at")

    if exclude_application_id:
        qs = qs.exclude(id=exclude_application_id)

    history = []

    for app in qs:
        history.append({
            "application_id": str(app.id),
            "job_id": str(app.job.id) if app.job else None,
            "job_title": app.job.job_title if app.job else None,
            "status": app.status,
            "match_score": float(app.match_score) if app.match_score else None,
            "created_at": app.created_at.isoformat(),
            "source": app.source,
            "is_duplicate": app.is_duplicate,
        })

    return history
