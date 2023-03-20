import os
from typing import AsyncIterator, Optional

import asyncssh
from asyncssh.sftp import *
from fastapi import FastAPI
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import StreamingResponse
from starlette.requests import Request
from streaming_form_data import StreamingFormDataParser
from streaming_form_data.targets import ValueTarget
import uvicorn

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


async def xx(async_gen, parser, data):
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


_SFTPPath = Union[bytes, FilePath]


class MyFTPClient(asyncssh.sftp.SFTPClient):
    async def aput(
        self,
        file_stream,
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


asyncssh.sftp.SFTPClient = MyFTPClient


async def run_client(async_gen, parser, data, remote_path) -> None:
    async with asyncssh.connect(
        os.environ.get("SFTP_SERVER"),
        1443,
        password="tiger",
        username="testuser",
        known_hosts=None,
    ) as conn:
        async with conn.start_sftp_client() as sftp:
            file_stream = StreamingBody(xx(async_gen, parser, data))
            await sftp.aput(file_stream, remote_path)


# try:
#     asyncio.get_event_loop().run_until_complete(run_client())
# except (OSError, asyncssh.Error) as exc:
#     sys.exit('SFTP operation failed: ' + str(exc))


@app.post("/files/")
async def create_file(request: Request, remote_path: str):
    parser = StreamingFormDataParser(headers=request.headers)
    data = ValueTarget()
    parser.register("file", data)
    await run_client(request.stream(), parser, data, remote_path)
    return dict(code="success")


@app.post("/test_files/")
async def test_files(request: Request):
    with open("./test.dat", "w+b") as f:
        async for each in request.stream():
            f.write(each)
    return dict(code="success")

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

class MySFTPClientWithDownload(asyncssh.sftp.SFTPClient):
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

asyncssh.sftp.SFTPClient = MySFTPClientWithDownload

async def download_file(remote_path: str) -> AsyncIterator[bytes]:
    async with asyncssh.connect(
        os.environ.get("SFTP_SERVER"),
        1443,
        password="tiger",
        username="testuser",
        known_hosts=None,
    ) as conn:
        async with conn.start_sftp_client() as sftp:
            async for chunk in sftp.aget(remote_path):
                yield chunk

@app.get("/files/{remote_path}")
async def get_file(remote_path: str):
    response = StreamingResponse(download_file(remote_path), media_type="application/octet-stream")
    response.headers["Content-Disposition"] = f"attachment; filename={remote_path}"
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
                folder_contents = await sftp.listdir(remote_path)
                return folder_contents

    contents = await get_folder_contents(remote_path)
    return {"folder_contents": contents}
if __name__ == '__main__':
    uvicorn.run(app)
