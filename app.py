from __future__ import annotations

import io
import os
import re
from collections import Counter
from typing import Any

import pandas as pd
from flask import Flask, jsonify, render_template, request
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024  # 5 MB upload limit
analyzer = SentimentIntensityAnalyzer()

THEME_KEYWORDS = {
    "Performance": ["slow", "fast", "lag", "loading", "speed", "crash", "freeze", "hang"],
    "Usability": ["easy", "difficult", "confusing", "simple", "navigation", "interface", "design"],
    "Pricing": ["price", "pricing", "expensive", "cheap", "cost", "subscription", "affordable"],
    "Features": ["feature", "option", "function", "missing", "request", "add", "support"],
    "Reliability": ["bug", "error", "broken", "fail", "issue", "problem", "work", "reliable"],
    "Customer Support": ["support team", "customer service", "response", "help desk", "representative"],
}


def classify_sentiment(text: str) -> dict[str, Any]:
    """Classify sentiment using VADER's rule/lexicon-based NLP sentiment model."""
    scores = analyzer.polarity_scores(text)
    compound = scores["compound"]
    if compound >= 0.05:
        label = "Positive"
    elif compound <= -0.05:
        label = "Negative"
    else:
        label = "Neutral"
    return {"sentiment": label, "score": round(compound, 3), "positive_score": round(scores["pos"], 3),
            "neutral_score": round(scores["neu"], 3), "negative_score": round(scores["neg"], 3)}


def detect_themes(text: str) -> list[str]:
    normalized = text.lower()
    return [theme for theme, words in THEME_KEYWORDS.items()
            if any(re.search(r"\b" + re.escape(word) + r"\b", normalized) for word in words)]


def analyze_reviews(reviews: list[str]) -> dict[str, Any]:
    cleaned = [str(review).strip() for review in reviews if review is not None and str(review).strip()]
    if not cleaned:
        raise ValueError("Enter at least one non-empty review to analyze.")
    if len(cleaned) > 1000:
        raise ValueError("Please analyze no more than 1,000 reviews at a time.")

    results = []
    theme_counts: Counter[str] = Counter()
    for index, review in enumerate(cleaned, start=1):
        sentiment = classify_sentiment(review)
        themes = detect_themes(review)
        theme_counts.update(themes)
        results.append({"id": index, "review": review, **sentiment,
                        "themes": themes, "theme_text": ", ".join(themes) if themes else "Other"})

    sentiment_counts = Counter(row["sentiment"] for row in results)
    negative_themes = Counter()
    positive_themes = Counter()
    for row in results:
        if row["sentiment"] == "Negative":
            negative_themes.update(row["themes"])
        elif row["sentiment"] == "Positive":
            positive_themes.update(row["themes"])

    pain_points = [theme for theme, _ in negative_themes.most_common(3)]
    strengths = [theme for theme, _ in positive_themes.most_common(3)]
    recommendations = []
    recommendation_map = {
        "Performance": "Investigate slow screens and crashes; measure load time before and after fixes.",
        "Usability": "Review navigation with users and simplify confusing workflows.",
        "Pricing": "Review plan value and explain pricing clearly before checkout.",
        "Features": "Group feature requests and prioritize them by frequency and customer impact.",
        "Reliability": "Reproduce reported errors and add regression tests for fixes.",
        "Customer Support": "Track first-response time and improve support follow-up.",
    }
    for theme in pain_points:
        if theme in recommendation_map:
            recommendations.append({"theme": theme, "action": recommendation_map[theme]})
    if not recommendations:
        recommendations.append({"theme": "General", "action": "Collect more specific feedback and monitor sentiment as new reviews arrive."})

    total = len(results)
    return {
        "total": total,
        "sentiment_counts": {label: sentiment_counts.get(label, 0) for label in ["Positive", "Neutral", "Negative"]},
        "sentiment_percentages": {label: round(sentiment_counts.get(label, 0) * 100 / total, 1)
                                  for label in ["Positive", "Neutral", "Negative"]},
        "theme_counts": [{"theme": theme, "count": count} for theme, count in theme_counts.most_common()],
        "pain_points": pain_points,
        "strengths": strengths,
        "recommendations": recommendations,
        "results": results,
        "method": "VADER sentiment analysis with rule-based theme detection",
    }


def read_reviews_from_csv(file_storage) -> list[str]:
    filename = (file_storage.filename or "").lower()
    if not filename.endswith(".csv"):
        raise ValueError("Please upload a .csv file.")
    raw = file_storage.read()
    if len(raw) > 5 * 1024 * 1024:
        raise ValueError("The CSV file must be 5 MB or smaller.")
    try:
        dataframe = pd.read_csv(io.BytesIO(raw))
    except Exception as exc:
        raise ValueError("Could not read this CSV. Please check that it is a valid comma-separated file.") from exc
    if dataframe.empty or len(dataframe.columns) == 0:
        raise ValueError("The CSV file has no review rows.")
    normalized = {str(column).strip().lower(): column for column in dataframe.columns}
    candidates = ["review", "reviews", "feedback", "comment", "comments", "text", "customer_review"]
    column = next((normalized[name] for name in candidates if name in normalized), None)
    if column is None:
        if len(dataframe.columns) == 1:
            column = dataframe.columns[0]
        else:
            raise ValueError("Could not identify a review column. Use a column named review, feedback, comment, or text.")
    reviews = dataframe[column].dropna().astype(str).tolist()
    if not any(review.strip() for review in reviews):
        raise ValueError("No non-empty reviews were found in the CSV file.")
    return reviews


@app.get("/")
def home():
    return render_template("index.html")


@app.get("/health")
def health():
    return jsonify({"status": "ok", "service": "product-feedback-analyser"})


@app.post("/api/analyze")
def analyze_api():
    data = request.get_json(silent=True) or {}
    reviews = data.get("reviews")
    if not isinstance(reviews, list):
        text = data.get("text", "")
        reviews = str(text).splitlines()
    try:
        return jsonify(analyze_reviews(reviews))
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400


@app.post("/api/analyze-csv")
def analyze_csv_api():
    uploaded = request.files.get("file")
    if not uploaded or not uploaded.filename:
        return jsonify({"error": "Choose a CSV file first."}), 400
    try:
        reviews = read_reviews_from_csv(uploaded)
        return jsonify(analyze_reviews(reviews))
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400


@app.errorhandler(413)
def file_too_large(_error):
    return jsonify({"error": "Upload is too large. The maximum file size is 5 MB."}), 413


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "5000")), debug=False)
