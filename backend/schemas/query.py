from typing import Optional
from pydantic import BaseModel

class QueryRequest(BaseModel):
    prompt: str
    system_prompt: Optional[str] = None
    model: str = "llama3.2"
    temperature: Optional[float] = 0.7
    stream: bool = False
