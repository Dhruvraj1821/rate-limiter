from locust import HttpUser, task, between

class RateLimiterUser(HttpUser):
    wait_time = between(0.01, 0.05)

    @task
    def check(self):
        self.client.post("/check", json={"client_id": "load-test-user"},
                          headers={"x-api-key": "key"})