import os
import time
import asyncio
import aiohttp
from pathlib import Path

API_URL = os.getenv("PIXELPURITAN_API_URL", "http://localhost:8000/v1/detect")
CONCURRENCY = int(os.getenv("BENCH_CONCURRENCY", "4"))
ROUNDS = int(os.getenv("BENCH_ROUNDS", "50"))
API_KEY = os.getenv("PIXELPURITAN_API_KEY")

IMG_PATH = os.getenv("BENCH_IMAGE", "./server/sample.png")

async def one(session, payload):
    t0 = time.perf_counter()
    async with session.post(API_URL, data=payload) as resp:
        await resp.read()
        return resp.status, time.perf_counter() - t0

async def main():
    if not Path(IMG_PATH).exists():
        print(f"Image not found: {IMG_PATH}")
        return
    img_bytes = Path(IMG_PATH).read_bytes()
    headers = {"X-API-Key": API_KEY} if API_KEY else {}
    form = aiohttp.FormData()
    form.add_field('file', img_bytes, filename='bench.png', content_type='image/png')

    sem = asyncio.Semaphore(CONCURRENCY)
    async with aiohttp.ClientSession(headers=headers) as session:
        latencies = []
        statuses = []
        async def run_one():
            async with sem:
                s, l = await one(session, form)
                statuses.append(s)
                latencies.append(l)
        tasks = [run_one() for _ in range(ROUNDS)]
        t0 = time.perf_counter()
        await asyncio.gather(*tasks)
        total = time.perf_counter() - t0
        ok = sum(1 for s in statuses if s == 200)
        print(f"Rounds: {ROUNDS}, Concurrency: {CONCURRENCY}")
        print(f"OK: {ok}, Fail: {ROUNDS-ok}")
        if latencies:
            print(f"Latency: avg={sum(latencies)/len(latencies):.3f}s, min={min(latencies):.3f}s, max={max(latencies):.3f}s")
        print(f"Total time: {total:.3f}s, Throughput: {ROUNDS/total:.2f} req/s")

if __name__ == "__main__":
    asyncio.run(main())
