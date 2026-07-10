from locust import HttpUser, task, between, events
import requests
import random
import logging

PROMPTS = [
    "What is machine learning?",
    "Explain machine learning to me",
    "How does machine learning work?",
    "What is deep learning?",
    "Explain neural networks",
    "What is a transformer model?",
    "How does GPT work?",
    "What is natural language processing?",
    "Explain NLP in simple terms",
    "What is a vector embedding?",
    "How do embeddings work?",
    "What is semantic search?",
    "Explain the difference between AI and ML",
    "What is supervised learning?",
    "What is unsupervised learning?",
]

SHARED_TOKEN = None

@events.init.add_listener
def on_locust_init(environment, **kwargs):
    global SHARED_TOKEN
    resp = requests.post(
        f"{environment.host}/auth/login",
        json={"email": "testuser@test.com", "password": "testpassword"}
    )
    SHARED_TOKEN = resp.json()["access_token"]


class GatewayUser(HttpUser):
    wait_time = between(0.1, 0.5)

    def auth_headers(self):
        return {"Authorization": f"Bearer {SHARED_TOKEN}"}

    @task
    def cached_query(self):
        prompt = random.choice(PROMPTS)
        with self.client.post("/query/", json={"prompt": prompt}, headers=self.auth_headers(), catch_response=True) as resp:
            if resp.status_code == 200:
                data = resp.json()
                logging.info(f"[cached] {resp.status_code} | cache_hit={data.get('cache_hit')} | {prompt[:40]}")
            else:
                resp.failure(f"status={resp.status_code}")
