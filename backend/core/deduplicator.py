import asyncio

inflight: dict[str, asyncio.Future] = {}
lock = asyncio.Lock()

async def deduplicate(prompt: str, call_llm_fn):
    first = False
    async with lock:
        if prompt in inflight:
            future = inflight[prompt]
        else:
            future = asyncio.get_running_loop().create_future()
            inflight[prompt] = future
            first = True
        
    if first:
        try:
            result = await call_llm_fn()
            future.set_result(result)
        except Exception as e:
            future.set_exception(e)
        finally:
            async with lock:
                del inflight[prompt]
        return result
    else:
        return await future