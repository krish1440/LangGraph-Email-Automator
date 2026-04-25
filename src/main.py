import os
import re
import base64
from typing import TypedDict, List, Optional
from datetime import datetime

from dotenv import load_dotenv
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from email.mime.text import MIMEText

from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, END

# Load environment variables
load_dotenv()

# Configuration
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GMAIL_TOKEN_PATH = "token.json"
MODEL_NAME = "gemini-2.5-flash"

# Define the State
class AgentState(TypedDict):
    emails: List[dict]
    current_email: Optional[dict]
    extracted_data: Optional[dict]
    reply_content: Optional[str]
    source_website: Optional[str]
    status: str

# --- Nodes ---

def fetch_emails(state: AgentState):
    """Fetch new form submission emails from Gmail."""
    if not os.path.exists(GMAIL_TOKEN_PATH):
        return {"status": "Error: token.json missing"}

    creds = Credentials.from_authorized_user_file(GMAIL_TOKEN_PATH)
    service = build('gmail', 'v1', credentials=creds)

    try:
        # Search for unread form submissions from Web3Forms
        query = 'is:unread subject:"New Form Submission from your Website"'
        results = service.users().messages().list(userId='me', q=query).execute()
        messages = results.get('messages', [])

        def get_body(payload):
            if 'parts' in payload:
                for part in payload['parts']:
                    if part['mimeType'] == 'text/plain':
                        return base64.urlsafe_b64decode(part['body']['data']).decode()
                    if 'parts' in part:
                        body = get_body(part)
                        if body: return body
            elif 'body' in payload and 'data' in payload['body']:
                return base64.urlsafe_b64decode(payload['body']['data']).decode()
            return ""

        emails_to_process = []
        for msg in messages:
            msg_data = service.users().messages().get(userId='me', id=msg['id']).execute()
            payload = msg_data.get('payload', {})
            headers = payload.get('headers', [])
            
            subject = next((h['value'] for h in headers if h['name'] == 'Subject'), "")
            body = get_body(payload)

            emails_to_process.append({
                "id": msg['id'],
                "threadId": msg['threadId'],
                "subject": subject,
                "body": body
            })

        return {"emails": emails_to_process, "status": "Fetched emails"}
    except Exception as e:
        return {"status": f"Error fetching emails: {str(e)}"}

def parse_email(state: AgentState):
    """Use Gemini to parse the email body and detect the source."""
    if not state['emails']:
        return {"status": "No emails to process"}

    email = state['emails'][0]
    body = email['body']

    llm = ChatGoogleGenerativeAI(model=MODEL_NAME, google_api_key=GOOGLE_API_KEY)
    
    prompt = f"""
    Analyze the following email body from a website form submission:
    ---
    {body}
    ---
    
    Extract the following details in a clear format:
    1. Name of the person
    2. Their Email address
    3. Their Phone/Mobile number
    4. Their Message
    5. Which website is this from? 
       - If it mentions 'abhay engineering' or 'dairy' or 'travis', it is 'abhay'.
       - If it mentions 'portfolio' or 'krish chaudhary' or 'data science' or 'projects', it is 'portfolio'.
       - Otherwise, say 'none'.

    Return ONLY a valid JSON object like this:
    {{"name": "...", "email": "...", "phone": "...", "message": "...", "source": "abhay/portfolio/none"}}
    """

    response = llm.invoke(prompt)
    import json
    # Clean the response string in case it has markdown blocks
    clean_content = response.content.replace("```json", "").replace("```", "").strip()
    data = json.loads(clean_content)

    print(f"DEBUG: LLM Parsed Name: {data['name']}")
    print(f"DEBUG: LLM Detected Source: {data['source']}")

    return {
        "current_email": email,
        "extracted_data": {
            "name": data['name'],
            "email": data['email'],
            "phone": data.get('phone', 'Not provided'),
            "message": data['message'],
            "sent_from": data['source']
        },
        "source_website": data['source'],
        "status": f"Parsed email via AI (Source: {data['source']})"
    }

def generate_reply(state: AgentState):
    """Generate a reply using Gemini and the specific knowledge base."""
    if state['source_website'] == "none":
        return {"status": "Skipping: Unrecognized website"}

    # Load Knowledge Base
    kb_file = f"data/{'abhay_engineering' if state['source_website'] == 'abhay' else 'portfolio_krish'}.md"
    with open(kb_file, "r") as f:
        kb_content = f.read()

    llm = ChatGoogleGenerativeAI(model=MODEL_NAME, google_api_key=GOOGLE_API_KEY)
    
    sign_off = "Krish Chaudhary" if state['source_website'] == "portfolio" else "Abhay Engineering"

    prompt = f"""
    You are an assistant for {state['source_website'].upper()}. 
    Below is the knowledge base for this entity:
    {kb_content}

    A new form submission was received from:
    Name: {state['extracted_data']['name']}
    Phone: {state['extracted_data']['phone']}
    Message: {state['extracted_data']['message']}

    Write a professional, short, and helpful reply to this person. 
    Acknowledge their message and offer next steps if applicable.
    Sign off as: {sign_off}
    """

    response = llm.invoke(prompt)
    
    return {"reply_content": response.content, "status": "Generated reply"}

def send_email(state: AgentState):
    """Send the generated reply back to the user."""
    if not state.get('reply_content'):
        return {"status": "No reply to send"}

    creds = Credentials.from_authorized_user_file(GMAIL_TOKEN_PATH)
    service = build('gmail', 'v1', credentials=creds)

    try:
        # Create message
        message = MIMEText(state['reply_content'])
        message['to'] = state['extracted_data']['email']
        message['subject'] = f"Re: {state['current_email']['subject']}"
        
        # Add CC for Abhay Engineering
        if state.get('source_website') == "abhay":
            message['Cc'] = "enng28@yahoo.com"
        
        raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
        
        # Send message
        service.users().messages().send(userId='me', body={'raw': raw, 'threadId': state['current_email']['threadId']}).execute()

        # Mark original as read (remove UNREAD label)
        service.users().messages().batchModify(
            userId='me',
            body={'ids': [state['current_email']['id']], 'removeLabelIds': ['UNREAD']}
        ).execute()

        return {"status": "Sent email and marked as read"}
    except Exception as e:
        return {"status": f"Error sending email: {str(e)}"}

# --- Graph Construction ---

def create_graph():
    workflow = StateGraph(AgentState)

    workflow.add_node("fetch_emails", fetch_emails)
    workflow.add_node("parse_email", parse_email)
    workflow.add_node("generate_reply", generate_reply)
    workflow.add_node("send_email", send_email)

    workflow.set_entry_point("fetch_emails")
    
    workflow.add_edge("fetch_emails", "parse_email")
    
    # Conditional logic
    def should_reply(state: AgentState):
        source = state.get('source_website', 'none')
        if source and source != "none":
            return "generate_reply"
        return END

    workflow.add_conditional_edges("parse_email", should_reply)
    workflow.add_edge("generate_reply", "send_email")
    workflow.add_edge("send_email", END)

    return workflow.compile()

if __name__ == "__main__":
    app = create_graph()
    # Execute the graph with initialized state
    initial_state = {
        "emails": [],
        "current_email": None,
        "extracted_data": None,
        "reply_content": None,
        "source_website": "none",
        "status": "Starting"
    }
    result = app.invoke(initial_state)
    print(f"Final Status: {result['status']}")
