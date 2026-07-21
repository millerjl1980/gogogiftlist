import json
from urllib.parse import parse_qs, urlparse

from django.contrib.auth.models import User
from django.core import mail
from django.test import Client, TestCase, override_settings


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

    @override_settings(
        EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
        FRONTEND_URL="https://giftlist.example.com",
    )
    def test_password_reset_sends_a_link_and_accepts_a_new_password(self):
        user = User.objects.create_user("owner", "owner@example.com", "old-password")
        response = self.post("/api/auth/password-reset/", {"email": user.email})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("https://giftlist.example.com/?reset_uid=", mail.outbox[0].body)

        reset_url = next(line for line in mail.outbox[0].body.splitlines() if line.startswith("https://"))
        params = parse_qs(urlparse(reset_url).query)
        confirm = self.post(
            "/api/auth/password-reset/confirm/",
            {
                "uid": params["reset_uid"][0],
                "token": params["reset_token"][0],
                "password": "new-safe-password",
            },
        )
        self.assertEqual(confirm.status_code, 200)
        user.refresh_from_db()
        self.assertTrue(user.check_password("new-safe-password"))

    @override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
    def test_password_reset_does_not_disclose_unknown_email_addresses(self):
        response = self.post("/api/auth/password-reset/", {"email": "nobody@example.com"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(mail.outbox), 0)
