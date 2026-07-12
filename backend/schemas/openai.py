from pydantic import BaseModel
from typing import Optional, List
import time
import uuid



class Message(BaseModel):
    role: str  # "system", "user", "assistant"
    content: str


class ChatCompletionRequest(BaseModel):
    model: str = "llama3.2"
    messages: List[Message]
    temperature: Optional[float] = 0.7

class ChatCompletionChoice(BaseModel):
    index: int
    message: Message
    finish_reason: str

class ChatCompletionResponse(BaseModel):
    id: str
    object: str
    created: int
    model: str
    choices: List[ChatCompletionChoice]
    cache_hit: bool
    