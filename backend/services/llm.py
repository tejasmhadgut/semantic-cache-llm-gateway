import json
import httpx
from typing import AsyncGenerator
from core.config import settings


async def call_llm(prompt: str, system_prompt: str = None, model: str = "llama3.2") -> str:
    if model.startswith("gpt-"):
        return await call_openai(prompt, system_prompt, model)
    elif model.startswith("claude-"):
        return await call_anthropic(prompt, system_prompt, model)
    else:
        return await call_ollama(prompt, system_prompt, model)

async def stream_llm(prompt: str, system_prompt: str = None, model: str = "llama3.2") -> AsyncGenerator[str, None]:
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})
    async with httpx.AsyncClient(timeout=120.0) as client:
        async with client.stream(
            "POST",
            "http://host.docker.internal:11434/api/chat",
            json={"model": model, "messages": messages, "stream": True}
        ) as response:
            async for line in response.aiter_lines():
                if line:
                    data = json.loads(line)
                    token = data.get("message", {}).get("content", "")
                    if token:
                        yield token
                    if data.get("done"):
                        break

async def call_ollama(prompt: str, system_prompt: str = None, model: str = "llama3.2") -> str:
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})
    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(
            "http://host.docker.internal:11434/api/chat",
            json={"model": model, "messages": messages, "stream": False}
        )
        return response.json()["message"]["content"]

async def call_openai(prompt: str, system_prompt: str = None, model: str = "gpt-3.5-turbo") -> str:
    raise NotImplementedError("OpenAI provider not configured")

async def call_anthropic(prompt: str, system_prompt: str = None, model: str = "claude-3-haiku-20240307") -> str:
    raise NotImplementedError("Anthropic provider not configured")
