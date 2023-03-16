import asyncio
from typing import AsyncIterator, Optional
import asyncssh, sys
import os

from asyncssh.sftp import *

import asyncio

from fastapi import FastAPI
from starlette.requests import Request
from fastapi import Response
import os
from streaming_form_data import StreamingFormDataParser
from streaming_form_data.targets import ValueTarget

app = FastAPI()

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
                print('read finish break')
                break

            content += chunk
            bytes_read += len(chunk)
            print(f'bytes_read {bytes_read}')

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

class MySFTPFileCopier(asyncssh.sftp._SFTPFileCopier):
    async def run(self, async_gen, parser, data) -> None:
        """Perform parallel file copy"""

        try:
            self._src = StreamingBody(async_gen)
            self._dst = await self._dstfs.open(self._dstpath, 'wb')

            _size = 4*1024*1024
            _buffer = b''
            while True:
                _chunk = await self._src.read(_size)
                print('chunk size', len(_chunk))
                parser.data_received(_chunk)
                if not data.value and len(_chunk) == _size:
                    continue
                if data.value:
                    await self._dst.write(data.value)
                    data._values.clear() #?
                if len(_chunk) < _size:
                    break
        finally:

            if self._dst: # pragma: no branch
                await self._dst.close()
    pass

_SFTPPath = Union[bytes, FilePath]

class MyFTPClient(asyncssh.sftp.SFTPClient):
    async def aput(self, async_gen, parser, data,
                  remotepath: Optional[_SFTPPath] = None, *,
                  preserve: bool = False, recurse: bool = False,
                  follow_symlinks: bool = False,
                  block_size: int = SFTP_BLOCK_SIZE,
                  max_requests: int = 128,
                  progress_handler: SFTPProgressHandler = None,
                  error_handler: SFTPErrorHandler = None) -> None:
        await MySFTPFileCopier(block_size, max_requests, 0,
                               0, None, self,
                               None, remotepath, progress_handler).run(async_gen, parser, data)

asyncssh.sftp.SFTPClient = MyFTPClient

async def run_client(async_gen, parser, data) -> None:
    async with asyncssh.connect(os.environ.get('SFTP_SERVER'), 1443, password='tiger', username='testuser', known_hosts=None) as conn:
        async with conn.start_sftp_client() as sftp:
            await sftp.aput(async_gen, parser, data, 'Python26.tar')

# try:
#     asyncio.get_event_loop().run_until_complete(run_client())
# except (OSError, asyncssh.Error) as exc:
#     sys.exit('SFTP operation failed: ' + str(exc))

@app.post("/files/")
async def create_file(request: Request):
    parser = StreamingFormDataParser(headers=request.headers)
    data = ValueTarget()
    parser.register('file', data)
    await run_client(request.stream(), parser, data)
    return dict(code='success')

@app.post("/test_files/")
async def create_file(request: Request):
    with open('./test.dat', 'w+b') as f:
        async for each in request.stream():
            f.write(each)
    return dict(code='success')