# 🤖 LangGraph Email Automator & AI Sales Agent

![Gemini](https://img.shields.io/badge/Google_Gemini-2.5_Flash-4285F4?logo=google-gemini&logoColor=white)
![LangGraph](https://img.shields.io/badge/LangGraph-Orchestration-orange)
![Python](https://img.shields.io/badge/Python-3.12-blue?logo=python&logoColor=white)
![Gmail](https://img.shields.io/badge/Gmail_API-v1-EA4335?logo=gmail&logoColor=white)

**Live Sites:** [Abhay Engineering](https://www.abhayengineering.in/) | [Personal Portfolio](https://krish-chaudhary.me/)

An advanced, dual-purpose email automation engine powered by **LangGraph** and **Gemini 2.5 Flash**. This system acts as a 24/7 intelligent responder for both personal portfolio inquiries and business leads (Abhay Engineering), providing contextual, AI-generated replies based on unique knowledge bases.

---

## 🌟 Key Features
- **Contextual Routing:** Automatically detects if an inquiry is for the Business or Personal site using LLM-based parsing.
- **Dynamic Knowledge Retrieval:** Uses separate Markdown-based knowledge bases to provide accurate, specific product or project details.
- **Smart Logic:** 
    - **Sales Agent (Abhay):** Handles pricing inquiries professionally, collects lead details, and CCs the main office.
    - **Personal Assistant (Portfolio):** Friendly, humble responses that avoid over-sharing unless specific technical questions are asked.
- **Zero-Touch Automation:** Deployed via GitHub Actions to run every 15 minutes for free.
- **State Management:** Built with a state-machine architecture (LangGraph) for reliable data flow and error handling.

---

## 📂 Project Architecture & File Breakdown

### 🏗️ Core Logic
- **`src/main.py`**: The heart of the system. It defines the `StateGraph`, including nodes for fetching, parsing, generating, and sending emails. It utilizes conditional edges for smart routing.
- **`src/auth_gmail.py`**: A dedicated utility script to handle the OAuth2 flow with Google APIs and generate the persistent `token.json`.

### 📚 Knowledge Base (`/data`)
- **`data/abhay_engineering.md`**: Detailed technical specs, pricing policies, and response guidelines for the engineering firm.
- **`data/portfolio_krish.md`**: Comprehensive record of Krish's AI/ML projects, skills, and personal communication style.

### ⚙️ Configuration & DevOps
- **`.github/workflows/main.yml`**: CI/CD pipeline that triggers the automation on a cron schedule (every 15 mins).
- **`.gitignore`**: Critical security file ensuring that `token.json`, `credentials.json`, and `.env` are never exposed in the public repository.
- **`requirements.txt`**: List of enterprise-grade libraries used, including `langgraph`, `langchain-google-genai`, and `google-api-python-client`.

---

## 🛠️ Setup & Installation

### 1. Google Cloud Configuration
1. Enable **Gmail API** in your GCP Console.
2. Create **OAuth 2.0 Credentials (Desktop App)**.
3. Download the JSON, rename it to `credentials.json`, and place it in the root directory.

### 2. Environment Setup
```bash
pip install -r requirements.txt
cp .env.example .env
```
Add your `GOOGLE_API_KEY` from Google AI Studio to the `.env` file.

### 3. Authentication
Run the one-time authentication script:
```bash
python src/auth_gmail.py
```
This generates the `token.json` required for headless automation.

---

## 🚀 Deployment (24/7 Automation)

This project is designed to run in a "Serverless" fashion using GitHub Actions.

1.  **Push** this code to your GitHub repository.
2.  **Add Secrets**: Go to **Settings > Secrets and variables > Actions** and add:
    - `GOOGLE_API_KEY`: Your Gemini API Key.
    - `GMAIL_TOKEN_JSON`: The full text content of your `token.json` file.
3.  The workflow will now execute every 15 minutes, check your inbox, and handle your leads automatically!

---

## 🛠️ Technologies Used
- **Orchestration:** LangGraph
- **LLM:** Google Gemini 2.0 Flash
- **Framework:** LangChain
- **API:** Google Gmail API v1
- **Automation:** GitHub Actions
