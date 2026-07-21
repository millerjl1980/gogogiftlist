import json

from django.test import Client, TestCase


class GiftListApiTests(TestCase):
    def setUp(self):
        self.client = Client(enforce_csrf_checks=True)
        self.client.get("/api/csrf/")

    def post(self, path, data):
        return self.client.post(
            path,
            data=json.dumps(data),
            content_type="application/json",
            HTTP_X_CSRFTOKEN=self.client.cookies["csrftoken"].value,
        )

    def test_health_check_is_public(self):
        response = self.client.get("/healthz")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})

    def test_owner_can_create_and_assign_a_gift(self):
        self.assertEqual(
            self.post(
                "/api/auth/register/",
                {"username": "owner", "email": "owner@example.com", "password": "safe-password"},
            ).status_code,
            201,
        )
        list_response = self.post(
            "/api/lists/",
            {"receiver": "Maya", "occasion": "Birthday", "date": "2026-05-18"},
        )
        self.assertEqual(list_response.status_code, 201)
        gift_list = list_response.json()["list"]
        giver_response = self.post(
            "/api/givers/", {"name": "Ava", "email": "ava@example.com"}
        )
        gift_response = self.post(
            f"/api/lists/{gift_list['id']}/gifts/",
            {"name": "A watercolor kit", "detail": "24 colors"},
        )
        assignment_response = self.post(
            f"/api/gifts/{gift_response.json()['gift']['id']}/assignment/",
            {"giver_id": giver_response.json()["giver"]["id"]},
        )
        self.assertEqual(assignment_response.status_code, 200)
        self.assertEqual(self.client.get("/api/lists/").json()["lists"][0]["gifts"][0]["giver_id"], giver_response.json()["giver"]["id"])
