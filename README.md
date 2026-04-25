# LangGraph Email Automator

This project automatically processes Web3Forms email notifications and replies to them using Gemini 2.0 Flash and LangGraph.

## Setup Instructions

### 1. Gmail API Setup
1. Go to the [Google Cloud Console](https://console.cloud.google.com/).
2. Create a new project.
3. Enable the **Gmail API**.
4. Go to **APIs & Services > OAuth consent screen**.
   - Select **External**.
   - Fill in the required app information.
   - Add your email (`krishchaudhary144@gmail.com`) to **Test users**.
5. Go to **APIs & Services > Credentials**.
   - Click **Create Credentials > OAuth client ID**.
   - Select **Desktop app**.
   - Name it "Email Automator" and click **Create**.
6. Download the JSON file, rename it to `credentials.json`, and place it in the root of this project.

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure Environment
1. Copy `.env.example` to `.env`.
2. Add your `GOOGLE_API_KEY` (from [Google AI Studio](https://aistudio.google.com/)).

### 4. Authenticate Gmail
Run the following script once. It will open your browser to log in.
```bash
python src/auth_gmail.py
```
This will create a `token.json` file. **Keep this file secure.**

### 5. Customize Knowledge Base
Edit the files in the `data/` folder to provide accurate information for the AI to use in its replies.
- `data/abhay_engineering.md`
- `data/portfolio_krish.md`

### 6. Run the Automator
To check for new emails and reply:
```bash
python src/main.py
```

## Automation (GitHub Actions)
To make this run 24/7 for free:
1. Create a private GitHub repository.
2. Add your code (except `token.json` and `.env`).
3. Add `GOOGLE_API_KEY` and the contents of `token.json` to **GitHub Actions Secrets**.
4. Set up a workflow to run `src/main.py` on a schedule.
