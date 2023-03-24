import asyncio
import time

import asyncssh


async def copy_file(source, dest):
    async with asyncssh.connect(
        "10.0.10.141", username="root", known_hosts=None
    ) as source_conn:
        async with asyncssh.connect(
            "10.0.10.141",
            port=2022,
            username="testuser",
            password="tiger",
            known_hosts=None,
        ) as dest_conn:
            async with source_conn.start_sftp_client() as source_sftp:
                async with dest_conn.start_sftp_client() as dest_sftp:
                    async with source_sftp.open(source, "rb") as source_file:
                        source_stat = await source_sftp.stat(source)
                        file_size = source_stat.size
                        start_time = time.monotonic()
                        async with dest_sftp.open(dest, "wb") as dest_file:
                            _size = 4 * 1024 * 1024
                            while True:
                                chunk = await source_file.read(_size)
                                if chunk:
                                    await dest_file.write(chunk)
                                if len(chunk) < _size:
                                    break
                        end_time = time.monotonic()
                        elapsed_time = end_time - start_time
                        print(
                            f"File Name:go1.20.2.linux-amd64.tar.gz
"
                            f"Size: {file_size} bytes. Time elapsed: {elapsed_time} seconds
"
                            f". Chunk size: {_size} bytes."
                        )
async with source_sftp.open(source, "rb") as source_file:
    source_stat = await source_sftp.stat(source)
    file_size = source_stat.size
    start_time = time.monotonic()
    _size = 4 * 1024 * 1024
    for i in range(0, file_size, _size):
        async with dest_sftp.open(dest, "ab") as dest_file:
            source_file.seek(i)
            chunk = await source_file.read(_size)
            await dest_file.write(chunk)
    end_time = time.monotonic()
    elapsed_time = end_time - start_time
    print(
        f"File Name:go1.20.2.linux-amd64.tar.gz
"
        f"Size: {file_size} bytes. Time elapsed: {elapsed_time} seconds
"
        f". Chunk size: {_size} bytes."
    )


async def main():
    await copy_file(
        "/root/test/go1.20.2.linux-amd64.tar.gz", "go1.20.2.linux-amd64.tar.gz"
    )


if __name__ == "__main__":
    asyncio.run(main())
