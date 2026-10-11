# SignalDesk — Product Feedback Analyser

A responsive Flask web application that helps product teams review customer feedback in batches, understand sentiment, spot recurring themes, and export results.

## Features

- Analyze pasted customer reviews, one review per line.
- Upload a CSV file with a `review`, `feedback`, `comment`, or `text` column.
- Sentiment classification using VADER (positive, neutral, negative) with a compound score.
- Rule-based theme detection for performance, usability, pricing, features, reliability, and customer support.
- Theme counts, pain points, strengths, and suggested next steps.
- Download row-level results as CSV.
- Input validation, a 5 MB upload limit, a 1,000-review batch limit, and a health endpoint.
- Unit and route tests.

## Technology stack

- **Frontend:** HTML, CSS, JavaScript
- **Backend:** Python, Flask
- **NLP:** VADER Sentiment (lexicon/rule-based sentiment analysis)
- **Data processing:** Pandas
- **Testing:** Python `unittest`
- **Deployment:** Gunicorn on Render

> Important: sentiment classification uses VADER, a lexicon- and rule-based NLP tool. Theme detection is rule-based. This project does not train a custom machine-learning model, and recommendations are mapped from detected themes. Treat results as decision support rather than ground truth.

## Run locally (Windows PowerShell)

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python app.py
```

Open `http://127.0.0.1:5000`.

## Run tests

```powershell
python -m unittest discover -s tests -v
```

## API endpoints

- `GET /health` — simple health check.
- `POST /api/analyze` — JSON with `{"reviews": ["review one", "review two"]}` or `{"text": "one review per line"}`.
- `POST /api/analyze-csv` — multipart form upload with field name `file`.

## Deploy to Render

1. Push the project folder contents to a GitHub repository.
2. In Render, select **New + → Web Service** and connect the repository.
3. Use these settings:
   - Runtime: **Python 3**
   - Branch: `main`
   - Root Directory: leave blank if the files are at repository root
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn app:app`
4. Choose a free instance if available and click **Deploy Web Service**.
5. Once live, check `/health` at the URL Render assigns.

No API keys or environment variables are required. Free hosting availability and limits may change.

## Example CSV

Create a CSV named `reviews.csv`:

```csv
review
"I love the clean design and easy navigation."
"The app is slow and sometimes crashes."
"Please add dark mode."
```

## Future improvements

- Persist feedback history in SQLite or PostgreSQL with explicit privacy controls.
- Add model evaluation on a labelled dataset before choosing a trained sentiment model.
- Add authentication and user-specific workspaces if the application is expanded beyond a demo.
- Improve theme detection using a labelled dataset or semantic clustering.
