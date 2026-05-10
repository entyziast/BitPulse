from locust import FastHttpUser, task, constant, between
import uuid


class BitPulseUser(FastHttpUser):
    wait_time = between(0.1, 0.3)
    
    def on_start(self):
        self.username = f"test_{uuid.uuid4().hex[:8]}"
        self.password = "strong_password123"
        self.email = f"{self.username}@example.com"
        
        register_payload = {
            "username": self.username,
            "email": self.email,
            "password": self.password
        }
        with self.client.post("/auth/registration", json=register_payload, catch_response=True) as response:
            if response.status_code == 201 or response.status_code == 200:
                response.success()
            else:
                response.failure(f"Registration failed: {response.text}")

        login_payload = {
            "username": self.username,
            "password": self.password
        }
        with self.client.post("/auth/login", data=login_payload, catch_response=True) as response:
            if response.status_code == 200:
                self.token = response.json().get("access_token")
                self.headers = {
                    "Authorization": f"Bearer {self.token}"
                }
            else:
                response.failure(f"Login failed: {response.text}")

    @task(10)
    def get_my_tickers(self):
        if hasattr(self, "headers"):
            self.client.get(
                "/tickers/my_tickers",
                headers=self.headers
            )

    @task(5)
    def get_alerts(self):
        if hasattr(self, "headers"):
            self.client.get(
                "/alerts/my_alerts",
                headers=self.headers
            )

    @task(1)
    def get_profile(self):
        if hasattr(self, "headers"):
            self.client.get(
                "/users/me",
                headers=self.headers
            )