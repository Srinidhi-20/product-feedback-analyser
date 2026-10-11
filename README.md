# ReviewLens — Product Feedback Analyser

A beginner-friendly Flask portfolio project that groups pasted customer reviews into themes, estimates sentiment with simple keyword rules, and suggests product improvements and success metrics.

## Run locally (Windows PowerShell)

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python app.py
```

Open http://127.0.0.1:5000

If PowerShell blocks activation, run this once in the current terminal:
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

## Deploy on Render

1. Push this folder to a GitHub repository.
2. In Render, choose **New + → Web Service** and connect the repository.
3. Use these settings:
   - Runtime: Python
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn app:app`
   - Root Directory: leave blank if the files are at the repository root.
4. Choose the Free instance if available and click Create Web Service.

No API key or environment variables are required for this version.

## Important method note

This version uses keyword rules, not a large language model or a trained ML model. Theme counts and sentiment are approximate. Verify the results manually before using them as research findings.
