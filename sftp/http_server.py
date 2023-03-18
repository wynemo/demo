import asyncio

from fastapi import FastAPI
from starlette.requests import Request
from fastapi import Response
import paramiko
import os
from fastapi.concurrency import run_in_threadpool

app = FastAPI()
from io import IOBase

def to_file_like_obj(iterable, base):
    chunk = base()
    offset = 0
    it = iter(iterable)

    def up_to_iter(size):
        nonlocal chunk, offset

        while size:
            if offset == len(chunk):
                try:
                    chunk = next(it)
                except StopIteration:
                    break
                else:
                    offset = 0
            to_yield = min(size, len(chunk) - offset)
            offset = offset + to_yield
            size -= to_yield
            yield chunk[offset - to_yield : offset]

    class FileLikeObj(IOBase):
        def readable(self):
            return True

        def read(self, size=-1):
            return base().join(
                up_to_iter(float('inf') if size is None or size < 0 else size)
            )
    return FileLikeObj()

def iter_over_async(ait, loop):
    ait = ait.__aiter__()
    async def get_next():
        try:
            obj = await ait.__anext__()
            return False, obj
        except StopAsyncIteration:
            return True, None
    while True:
        done, obj = loop.run_until_complete(get_next())
        if done:
            break
        yield obj
def get_results(ait):
    while True:
        try:
            yield asyncio.run(ait.__anext__())
        except StopAsyncIteration:
            break 
def transfer(_in, path):
    transport = paramiko.Transport((os.environ.get('SFTP_SERVER'),1443))

    # automatically add the host key for non-interactive authentication

    # connect to the server
    transport.connect(None, username='testuser', password='tiger')

    # create an SFTP client
    sftp = paramiko.SFTPClient.from_transport(transport)

    # upload the stream to the server
    sftp.putfo(_in, path')

    # close the SFTP session and SSH connection
    sftp.close()
    transport.close()

@app.post("/files/")
async def create_file(request: Request, remote_path):
    # loop = asyncio.get_event_loop()
    body = b''
    # sync_gen = iter_over_async(request.stream(), loop)
    sync_gen = get_results(request.stream())
    _file = to_file_like_obj(sync_gen, bytes)
    await run_in_threadpool(transfer, _file, remote_path)
    # transfer(_file)
    return dict(code='success')