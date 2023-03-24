import os
from typing import AsyncIterator, Optional, IO

import asyncssh
import uvicorn
from asyncssh.sftp import *
from fastapi import FastAPI
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import StreamingResponse
from starlette.requests import Request
from streaming_form_data import StreamingFormDataParser
from streaming_form_data.targets import ValueTarget

app = FastAPI()


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    print(
        "Time took to process the request and return response is {} sec".format(
            time.time() - start_time
        )
    )
    return response


class StreamingBody:
    _chunks: AsyncIterator[bytes]
    _backlog: bytes

    def __init__(self, chunks: AsyncIterator[bytes]):
        self._chunks = chunks
        self._backlog = b""

    async def _read_until_end(self):
        content = self._backlog
        self._backlog = b""

        while True:
            try:
                content += await self._chunks.__anext__()
            except StopAsyncIteration:
                break

        return content

    async def _read_chunk(self, size: int):
        content = self._backlog
        bytes_read = len(self._backlog)

        while bytes_read < size:
            try:
                chunk = await self._chunks.__anext__()
            except StopAsyncIteration:
                print("read finish break")
                break

            content += chunk
            bytes_read += len(chunk)
            print(f"bytes_read {bytes_read}")

        self._backlog = content[size:]
        content = content[:size]

        return content

    async def read(self, size: int = -1):
        if size > 0:
            return await self._read_chunk(size)
        elif size == -1:
            return await self._read_until_end()
        else:
            return b""


async def parse_file_gen(async_gen, parser, data):
    async for _chunk in async_gen:
        await run_in_threadpool(parser.data_received, _chunk)
        if not data.value:
            continue
        yield data.value
        data._values.clear()


class MySFTPFileCopier(asyncssh.sftp._SFTPFileCopier):
    async def run(self, file_stream) -> None:
        """Perform parallel file copy"""

        try:
            self._src = file_stream
            self._dst = await self._dstfs.open(self._dstpath, "wb")

            _size = 4 * 1024 * 1024
            while True:
                _chunk = await self._src.read(_size)
                print("chunk size", len(_chunk))
                if _chunk:
                    await self._dst.write(_chunk)
                if len(_chunk) < _size:
                    break
        finally:
            if self._dst:  # pragma: no branch
                await self._dst.close()


class MySFTPFileDownloader(asyncssh.sftp._SFTPFileCopier):
    async def run(self) -> AsyncIterator[bytes]:
        """Perform parallel file copy as a stream"""

        try:
            self._src = await self._srcfs.open(self._srcpath, "rb")
            _size = 4 * 1024 * 1024

            while True:
                _chunk = await self._src.read(_size)
                if _chunk:
                    yield _chunk
                if len(_chunk) < _size:
                    break
        finally:
            if self._src:  # pragma: no branch
                await self._src.close()


_SFTPPath = Union[bytes, FilePath]


class MySFTPClient(asyncssh.sftp.SFTPClient):
    async def aput(
        self,
        file_stream: IO,
        remotepath: Optional[_SFTPPath] = None,
        *,
        preserve: bool = False,
        recurse: bool = False,
        follow_symlinks: bool = False,
        block_size: int = SFTP_BLOCK_SIZE,
        max_requests: int = 128,
        progress_handler: SFTPProgressHandler = None,
        error_handler: SFTPErrorHandler = None,
    ) -> None:
        await MySFTPFileCopier(
            block_size,
            max_requests,
            0,
            0,
            None,
            self,
            None,
            remotepath,
            progress_handler,
        ).run(file_stream)

    def aget(
        self,
        remotepath: Optional[_SFTPPath] = None,
        *,
        block_size: int = SFTP_BLOCK_SIZE,
        max_requests: int = 128,
        progress_handler: SFTPProgressHandler = None,
        error_handler: SFTPErrorHandler = None,
    ) -> AsyncIterator[bytes]:
        return MySFTPFileDownloader(
            block_size,
            max_requests,
            0,
            0,
            self,
            None,
            remotepath,
            None,
            progress_handler,
        ).run()


asyncssh.sftp.SFTPClient = MySFTPClient


async def run_client(async_gen, parser, data, remote_path) -> None:
    async with asyncssh.connect(
        os.environ.get("SFTP_SERVER"),
        1443,
        password="tiger",
        username="testuser",
        known_hosts=None,
    ) as conn:
        sftp: MySFTPClient
        async with conn.start_sftp_client() as sftp:
            file_stream = StreamingBody(parse_file_gen(async_gen, parser, data))
            await sftp.aput(file_stream, remote_path)


@app.post("/files/")
async def create_file(request: Request, remote_path: str):
    parser = StreamingFormDataParser(headers=request.headers)
    data = ValueTarget()
    parser.register("file", data)
    await run_client(request.stream(), parser, data, remote_path)
    return dict(code="success")


@app.post("/raw_files/")
async def test_files(request: Request):
    """
    curl -X POST --data-binary "@/tmp/go1.20.2.linux-arm64.tar.gz" http://127.0.0.1:8000/raw_files/
    """
    with open("./test.dat", "w+b") as f:
        async for each in request.stream():
            f.write(each)
    return dict(code="success")


@app.post("/part_upload_files/")
async def part_upload_files(request: Request, remote_path: str):
    headers = request.headers
    file_size = int(headers.get("X-File-Size"))
    start_pos = int(headers.get("X-Start-Byte"))
    parser = StreamingFormDataParser(headers=headers)
    data = ValueTarget()
    parser.register("file", data)
    async with asyncssh.connect(
        os.environ.get("SFTP_SERVER"),
        1443,
        password="tiger",
        username="testuser",
        known_hosts=None,
    ) as conn:
        async with conn.start_sftp_client() as sftp:
            file_stream = StreamingBody(request.stream())
            remote_file = await sftp.open(remote_path)
            await remote_file.seek(start_pos)
            while True:
                _size = 4 * 1024 * 1024
                _chunk = await file_stream.read(_size)
                if _chunk:
                    await remote_file.write(_chunk)
                if len(_chunk) < _size:
                    break
    return dict(code="success")


async def download_file(remote_path: str) -> AsyncIterator[bytes]:
    async with asyncssh.connect(
        os.environ.get("SFTP_SERVER"),
        1443,
        password="tiger",
        username="testuser",
        known_hosts=None,
    ) as conn:
        sftp: MySFTPClient
        async with conn.start_sftp_client() as sftp:
            yield await sftp.getsize(remote_path)
            async for chunk in sftp.aget(remote_path):
                yield chunk


@app.get("/files/{remote_path}")
async def get_file(remote_path: str):
    _aiter = download_file(remote_path)
    size = await _aiter.__anext__()
    response = StreamingResponse(_aiter, media_type="application/octet-stream")
    response.headers["Content-Disposition"] = f"attachment; filename={remote_path}"
    response.headers["Content-Length"] = str(size)
    return response


@app.get("/list_folder/")
async def list_remote_sftp_folder(remote_path: str):
    async def get_folder_contents(remote_path: str) -> list:
        async with asyncssh.connect(
            os.environ.get("SFTP_SERVER"),
            1443,
            password="tiger",
            username="testuser",
            known_hosts=None,
        ) as conn:
            async with conn.start_sftp_client() as sftp:
                folder_contents = [
                    {"filename": each.filename, "attrs": str(each.attrs)}
                    async for each in sftp.scandir(remote_path)
                ]
                return folder_contents

    contents = await get_folder_contents(remote_path)
    return {"folder_contents": contents}

# api to delete files
@app.post('/delete_file')
async def delete_file(remote_path: str):
    async with asyncssh.connect(
        os.environ.get("SFTP_SERVER"),
        1443,
        password="tiger",
        username="testuser",
        known_hosts=None,
    ) as conn:
        sftp: MySFTPClient
        async with conn.start_sftp_client() as sftp:
            await sftp.remove(remote_path)
    return dict(code="success")

if __name__ == "__main__":
    uvicorn.run(app)
