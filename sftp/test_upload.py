import os
import asyncio
import httpx

async def upload_file(url: str, local_path: str, remote_path: str):
    file_size = os.path.getsize(local_path)
    chunk_size = 25 * 1024 * 1024
    headers = {
        # "Content-Length": str(chunk_size),
        "Content-Type": 'application/octet-stream',
        "X-File-Size": str(file_size),
        "X-Start-Byte": "0",
    }
    async with httpx.AsyncClient() as client:
        with open(local_path, "rb") as f:
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                response = await client.post(
                    url,
                    headers=headers,
                    content=chunk,
                    params={"remote_path": remote_path},
                    timeout = 30
                )
                headers["X-Start-Byte"] = str(int(headers["X-Start-Byte"]) + len(chunk))
                print(response)

asyncio.run(upload_file('http://127.0.0.1:8000/part_upload_files/', '/tmp/go1.20.2.linux-arm64.tar.gz', 'go1.20.2.linux-arm64.tar.gz'))