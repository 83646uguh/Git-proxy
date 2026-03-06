from fastapi import FastAPI, Response
import os

app = FastAPI()

PROXIES_FILE = 'working_proxies.txt'
PROXIES_PER_PAGE = 500

# Cache proxies in memory to avoid repeated file reads
cached_proxies = []
last_mtime = 0

def get_proxies():
    global cached_proxies, last_mtime
    if not os.path.exists(PROXIES_FILE):
        return []

    current_mtime = os.path.getmtime(PROXIES_FILE)
    if current_mtime > last_mtime:
        with open(PROXIES_FILE, 'r') as f:
            cached_proxies = [line.strip() for line in f if line.strip()]
        last_mtime = current_mtime

    return cached_proxies

@app.get("/page{page_num}")
async def get_page(page_num: int):
    proxies = get_proxies()

    if not proxies:
        return Response(content="No proxies available", media_type="text/plain")

    start_idx = (page_num - 1) * PROXIES_PER_PAGE
    end_idx = start_idx + PROXIES_PER_PAGE

    page_proxies = proxies[start_idx:end_idx]

    if not page_proxies or page_num < 1:
        return Response(content="No proxies available", media_type="text/plain")

    return Response(content="\n".join(page_proxies), media_type="text/plain")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
