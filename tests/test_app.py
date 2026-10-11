import io
import unittest

from app import app, analyze_reviews, classify_sentiment, detect_themes


class AnalysisTests(unittest.TestCase):
    def test_positive_sentiment(self):
        self.assertEqual(classify_sentiment("I absolutely love this excellent app!")["sentiment"], "Positive")

    def test_negative_sentiment(self):
        self.assertEqual(classify_sentiment("This app is terrible, slow, and frustrating.")["sentiment"], "Negative")

    def test_neutral_sentiment(self):
        self.assertEqual(classify_sentiment("The package arrived on Tuesday.")["sentiment"], "Neutral")

    def test_theme_detection(self):
        self.assertIn("Performance", detect_themes("The app is slow and loading takes too long."))

    def test_empty_reviews_raise_error(self):
        with self.assertRaises(ValueError):
            analyze_reviews(["", "  "])

    def test_analysis_summary(self):
        result = analyze_reviews(["Love the simple design", "The app is slow", "It arrived today"])
        self.assertEqual(result["total"], 3)
        self.assertEqual(sum(result["sentiment_counts"].values()), 3)


class RouteTests(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_health_route(self):
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["status"], "ok")

    def test_empty_analysis_returns_400(self):
        response = self.client.post("/api/analyze", json={"reviews": [""]})
        self.assertEqual(response.status_code, 400)

    def test_csv_upload(self):
        content = b"review\nI love this product\nThe app is slow\n"
        response = self.client.post("/api/analyze-csv", data={
            "file": (io.BytesIO(content), "reviews.csv")
        }, content_type="multipart/form-data")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["total"], 2)


if __name__ == "__main__":
    unittest.main()
