from openai import AzureOpenAI
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.shortcuts import render
import os
import re
from .utils.engine import retrieve_context
client = AzureOpenAI(api_key=settings.OPENAI_API_KEY,azure_endpoint=settings.ENDPOINT_URL,api_version="2024-05-01-preview")

def load_kb_file(relative_path):
    """
    Load a KB file from the static folder and return its text.
    """
    full_path = os.path.join(settings.BASE_DIR, "static", relative_path)

    with open(full_path, "r", encoding="utf-8") as f:
        return f.read()

# SYSTEM_PROMPT = load_kb_file("KB.txt")
SYSTEM_PROMPT = """
You are a professional HRMS support assistant for the Knowcraft system.

Your responsibilities:

- Answer user questions clearly and politely
- Use simple language understandable to non-technical users
- Provide step-by-step guidance when explaining processes
- Use the provided knowledge context to answer accurately
- If information is missing, politely ask for clarification
- Never make up information

If the knowledge context says LOW_CONFIDENCE:
→ Tell the user you are not sure and escalate politely.

Always maintain a helpful and professional tone.
"""
FUNCTIONS = [{
        "name": "save_details",
        "description": "Save details into Conversation model.",
        "parameters": {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "issue": {"type": "string"},
            },
            "required": [
                "name","issue"
            ]
        }
    }]
    
def markdown_to_html(text: str) -> str:
    if not text:
        return ""
    
    # Links: [text](url)
    # Allows http, https, and mailto links
    link_text = re.sub(
        r'\[([^\]]+)\]\((https?:\/\/[^\s)]+|mailto:[^\s)]+)\)',
        r'<a href="\2" target="_blank" rel="noopener noreferrer" style="color:blue;cursor:pointer;">\1</a>',
        text
    )
    if link_text:
        return link_text
    
    # Bold + Italic
    text = re.sub(r'\*\*\*(.+?)\*\*\*', r'<b><i>\1</i></b>', text)
    text = re.sub(r'___(.+?)___', r'<b><i>\1</i></b>', text)
    
    # Bold
    text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text)
    text = re.sub(r'__(.+?)__', r'<b>\1</b>', text)
    
    # Italic
    text = re.sub(r'\*(.+?)\*', r'<i>\1</i>', text)
    text = re.sub(r'_(.+?)_', r'<i>\1</i>', text)
    
    # Replace newlines with <br>
    text = text.replace("\n", "<br>")
    
    # Strip dangerous tags
    text = re.sub(r'<script.*?>.*?</script>', '', text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r'<style.*?>.*?</style>', '', text, flags=re.IGNORECASE | re.DOTALL)
    
    return text

@csrf_exempt
def support_bot(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            user_message = data.get("message", "").strip()
            session_key = "support_chat_history"

            if session_key not in request.session:
                history = [{"role": "system", "content": SYSTEM_PROMPT}]
                request.session[session_key] = {'history': history}
            else:
                history = request.session[session_key]['history']

            # ⭐ RAG Context Retrieval
            context = retrieve_context(user_message)

            # ⭐ Inject context into user message
            rag_prompt = f"""
            You must answer ONLY using the provided knowledge.
User Question:
{user_message}

Relevant Knowledge Base:
{context}
"""
            history.append({"role": "user", "content": rag_prompt})

            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=history,
                temperature=0.5
            )

            msg = response.choices[0].message

            bot_reply = msg.content.strip() if msg.content else ""
            bot_reply = markdown_to_html(bot_reply)

            history.append({"role": "assistant", "content": bot_reply})

            return JsonResponse({"reply": bot_reply})

        except Exception as e:
            print(e)
            return JsonResponse({"reply": "Sorry! I am not able to answer that."})