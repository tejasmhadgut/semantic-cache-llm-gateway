import httpx
from core.config import settings

import httpx
from core.config import settings

async def call_llm(prompt:str) -> str:
    async with httpx.AsyncClient(timeout=60.0) as  client:
        response = await client.post(
            "http://localhost:11434/api/generate",
            json={
                "model":"llama3.2",
                "prompt": prompt,
                "stream": False
            }
        )
        data = response.json()
        return data["response"]