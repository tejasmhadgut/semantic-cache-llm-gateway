import httpx
from core.config import settings


async def call_llm(prompt: str, system_prompt: str = None, model: str = "llama3.2") -> str:
    if model.startswith("gpt-"):
        return await call_openai(prompt, system_prompt, model)
    elif model.startswith("claude-"):
        return await call_anthropic(prompt, system_prompt, model)
    else:
        return await call_ollama(prompt, system_prompt, model)

async def call_ollama(prompt: str, system_prompt: str = None, model: str = "llama3.2") -> str:
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            "http://host.docker.internal:11434/api/chat",
            json={"model": model, "messages": messages, "stream": False}
        )
        return response.json()["message"]["content"]

async def call_openai(prompt: str, system_prompt: str = None, model: str = "gpt-3.5-turbo") -> str:
    # placeholder — requires OPENAI_API_KEY in config
    raise NotImplementedError("OpenAI provider not configured")

async def call_anthropic(prompt: str, system_prompt: str = None, model: str = "claude-3-haiku-20240307") -> str:
    # placeholder — requires ANTHROPIC_API_KEY in config
    raise NotImplementedError("Anthropic provider not configured")
