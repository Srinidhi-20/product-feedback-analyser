from flask import Flask, render_template, request
from collections import Counter, defaultdict
import re

app = Flask(__name__)

THEMES = {
    "Delivery issues": {
        "keywords": ["late", "delay", "delayed", "delivery", "delivered", "cold food", "missing item", "wrong order", "driver", "rider"],
        "feature": "Improve delivery estimates and provide clearer live order tracking.",
        "metric": "Reduce late deliveries and delivery-related complaints."
    },
    "Payment problems": {
        "keywords": ["payment", "paid", "charged", "refund", "refunded", "transaction", "upi", "card", "money deducted", "failed payment"],
        "feature": "Show clear payment status and provide a safe retry/refund flow.",
        "metric": "Reduce payment failures and payment-related support contacts."
    },
    "App usability": {
        "keywords": ["confusing", "difficult to use", "hard to find", "cannot find", "can't find", "navigation", "layout", "reorder", "slow app", "crash", "crashes", "bug"],
        "feature": "Simplify navigation and make frequently used actions easier to find.",
        "metric": "Increase task completion and successful repeat orders."
    },
    "Pricing and fees": {
        "keywords": ["expensive", "price", "pricing", "cost", "fee", "fees", "charges", "discount", "offer", "overpriced"],
        "feature": "Explain fees and discounts clearly before checkout.",
        "metric": "Reduce checkout abandonment linked to unexpected costs."
    },
    "Customer support": {
        "keywords": ["support", "customer care", "no response", "not responding", "help", "complaint", "agent", "contact"],
        "feature": "Make order-specific help easier to access and show support status.",
        "metric": "Reduce response time and repeat support requests."
    },
    "Food or product quality": {
        "keywords": ["taste", "tasteless", "quality", "stale", "spoiled", "damaged", "packaging", "portion", "quantity", "wrong item", "bad food"],
        "feature": "Improve quality reporting and make issue resolution easier.",
        "metric": "Reduce quality-related complaints and repeat incidents."
    },
    "Positive experience": {
        "keywords": ["great", "excellent", "amazing", "good service", "fast delivery", "easy to use", "love it", "helpful", "perfect", "delicious", "best app"],
        "feature": "Preserve the parts of the experience customers praise.",
        "metric": "Maintain or improve positive-review share."
    }
}

NEGATIVE_HINTS = ["bad", "worst", "poor", "late", "delay", "failed", "crash", "expensive", "confusing",
                  "refund", "problem", "issue", "terrible", "never", "not", "wrong", "cold", "stale", "broken"]
POSITIVE_HINTS = ["great", "excellent", "amazing", "good", "love", "perfect", "delicious", "fast", "helpful", "best"]

def analyse_reviews(raw_text):
    reviews = [line.strip(" \t-•") for line in raw_text.splitlines() if line.strip(" \t-•")]
    results = []
    theme_counts = Counter()
    theme_reviews = defaultdict(list)

    for review in reviews:
        lower = review.lower()
        matched = []
        for theme, info in THEMES.items():
            if any(keyword in lower for keyword in info["keywords"]):
                matched.append(theme)

        if not matched:
            matched = ["Other / uncategorised"]

        negative = sum(1 for word in NEGATIVE_HINTS if word in lower)
        positive = sum(1 for word in POSITIVE_HINTS if word in lower)
        sentiment = "Negative" if negative > positive else ("Positive" if positive > negative else "Mixed / unclear")

        results.append({"text": review, "themes": matched, "sentiment": sentiment})
        for theme in matched:
            theme_counts[theme] += 1
            theme_reviews[theme].append(review)

    rows = []
    for theme, count in theme_counts.most_common():
        info = THEMES.get(theme, {
            "feature": "Review this theme manually and decide whether a product change is needed.",
            "metric": "Define a measurable outcome after reviewing the underlying feedback."
        })
        if theme == "Other / uncategorised":
            priority = "Review"
        elif theme in ("Delivery issues", "Payment problems", "Customer support", "Food or product quality"):
            priority = "High" if count >= 2 else "Medium"
        else:
            priority = "High" if count >= 4 and theme != "Positive experience" else "Medium"
        rows.append({
            "theme": theme,
            "count": count,
            "examples": theme_reviews[theme][:2],
            "feature": info["feature"],
            "metric": info["metric"],
            "priority": priority
        })

    pain_points = [r for r in rows if r["theme"] != "Positive experience" and r["theme"] != "Other / uncategorised"][:3]
    sentiment_counts = Counter(r["sentiment"] for r in results)
    return {
        "reviews": results,
        "rows": rows,
        "pain_points": pain_points,
        "total": len(reviews),
        "sentiments": sentiment_counts
    }

@app.route("/", methods=["GET", "POST"])
def index():
    analysis = None
    raw_text = ""
    error = None
    if request.method == "POST":
        raw_text = request.form.get("reviews", "").strip()
        if not raw_text:
            error = "Paste at least one review, with each review on a separate line."
        else:
            analysis = analyse_reviews(raw_text)
            if analysis["total"] == 0:
                error = "No reviews were detected. Put each review on a separate line."
                analysis = None
    return render_template("index.html", analysis=analysis, raw_text=raw_text, error=error)

@app.route("/health")
def health():
    return {"status": "ok"}

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
