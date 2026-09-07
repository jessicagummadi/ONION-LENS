import sys
from pathlib import Path
root_dir = Path(__file__).resolve().parent.parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

import unittest
from fastapi.testclient import TestClient
from backend.app.main import app

class TestOnionLensAPI(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_health(self):
        res = self.client.get("/api/health")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "online")
        self.assertTrue(data["features"]["individual_onion_counting"])

    def test_auth_login(self):
        res = self.client.post("/api/auth/login", json={
            "inspector_id": "INSP-APMC-8492",
            "pin": "1234"
        })
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("access_token", data)
        self.assertEqual(data["user"]["inspector_id"], "INSP-APMC-8492")

    def test_analyze_sample(self):
        with open("static/images/samples/sample-lot-grade-a.jpg", "rb") as f:
            files = {"file": ("sample.jpg", f, "image/jpeg")}
            data = {"lot_id": "TEST-LOT-01", "variety": "Nashik Red"}
            res = self.client.post("/api/analyze", files=files, data=data)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data["is_onion"])
        self.assertGreater(data["total_onions"], 0)
        self.assertEqual(data["total_onions"], data["healthy_onions"] + data["defective_onions"])
        self.assertGreater(len(data["defects"]), 0)
        for d in data["defects"]:
            self.assertIn("affected_onion_count", d)
            self.assertIn("percentage", d)

    def test_get_inspections(self):
        res = self.client.get("/api/inspections")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("inspections", data)
        self.assertIsInstance(data["inspections"], list)

if __name__ == "__main__":
    unittest.main()
