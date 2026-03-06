import asyncio
import aiohttp
import re
import os
from aiohttp_proxy import ProxyConnector

# Configuration
SOURCE_FILE = 'AProxy.txt'
OUTPUT_FILE = 'working_proxies.txt'
CHECK_URL = 'https://httpbin.org/ip'
TIMEOUT = 5
CONCURRENCY = 500

async def fetch_proxies(session, url):
    try:
        async with session.get(url, timeout=10) as response:
            if response.status == 200:
                text = await response.text()
                # Find all IP:PORT patterns
                return re.findall(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:\d{1,5}', text)
    except Exception as e:
        print(f"Error fetching from {url}: {e}")
    return []

async def check_proxy(proxy, semaphore, working_proxies):
    async with semaphore:
        # According to requirements: "Use both http and https proxy formats"
        # Most of the sources in AProxy.txt are socks5, so we should also check that.
        # But specifically mentioned http and https.
        # aiohttp_proxy supports http, https, socks4, socks5.

        protocols = ['http', 'https', 'socks5']
        for proto in protocols:
            try:
                connector = ProxyConnector.from_url(f"{proto}://{proxy}")
                async with aiohttp.ClientSession(connector=connector) as session:
                    async with session.get(CHECK_URL, timeout=TIMEOUT) as response:
                        if response.status == 200:
                            working_proxies.add(proxy)
                            return
            except:
                continue

async def main():
    if not os.path.exists(SOURCE_FILE):
        print(f"{SOURCE_FILE} not found. Creating an empty one.")
        with open(SOURCE_FILE, 'w') as f:
            f.write("# Add proxy list URLs here, one per line\n")
        return

    with open(SOURCE_FILE, 'r') as f:
        urls = [line.strip() for line in f if line.strip() and not line.startswith('#')]

    if not urls:
        print("No URLs found in AProxy.txt")
        return

    async with aiohttp.ClientSession() as session:
        tasks = [fetch_proxies(session, url) for url in urls]
        results = await asyncio.gather(*tasks)

    all_proxies = set()
    for proxies in results:
        all_proxies.update(proxies)

    print(f"Total unique proxies found: {len(all_proxies)}")

    working_proxies = set()
    semaphore = asyncio.Semaphore(CONCURRENCY)

    tasks = [check_proxy(proxy, semaphore, working_proxies) for proxy in all_proxies]

    print(f"Checking {len(tasks)} proxies...")
    await asyncio.gather(*tasks)

    print(f"Found {len(working_proxies)} working proxies.")

    with open(OUTPUT_FILE, 'w') as f:
        for proxy in sorted(working_proxies):
            f.write(f"{proxy}\n")

if __name__ == '__main__':
    asyncio.run(main())
