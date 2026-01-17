import httpx

from app.infra.settings import settings


class OpenAIEmbeddingsClient:
    def __init__(self) -> None:
        self.api_key = settings.openai_api_key
        self.model = settings.openai_embeddings_model
        self.dimensions = settings.openai_embeddings_dim
        self.timeout = settings.openai_timeout_seconds

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []

        if not self.api_key:
            return []

        url = "https://api.openai.com/v1/embeddings"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "input": texts,
            "dimensions": self.dimensions,
        }

        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(url, headers=headers, json=payload)
                response.raise_for_status()
                data = response.json()
                embeddings = [item["embedding"] for item in data.get("data", [])]
                if len(embeddings) != len(texts):
                    return []
                return embeddings
        except (httpx.HTTPError, KeyError, TypeError):
            return []
