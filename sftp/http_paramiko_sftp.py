import os
import time

import paramiko
from fastapi import FastAPI
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import StreamingResponse
from starlette.requests import Request
from streaming_form_data import StreamingFormDataParser
from streaming_form_data.targets import BaseTarget

from util import time_it

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


# Configure SFTP connection details
sftp_host = os.environ.get("SFTP_SERVER")
sftp_port = os.environ.get("SFTP_PORT") or 1443
sftp_port = int(sftp_port)
sftp_username = os.environ.get("SFTP_USERNAME") or "testuser"
sftp_password = os.environ.get("SFTP_PASSWORD") or "tiger"


def create_sftp_client():
    # Create an SFTP client and connect to the server
    transport = paramiko.Transport((sftp_host, sftp_port))
    transport.connect(username=sftp_username, password=sftp_password)
    sftp = paramiko.SFTPClient.from_transport(transport)
    return transport, sftp


class MyTarget(BaseTarget):
    def __init__(self, obj):
        self.obj = obj
        super().__init__()

    def on_data_received(self, chunk: bytes):
        print("size", len(chunk))
        self.obj.write(chunk)


@app.post("/upload_file")
async def upload_file(request: Request, remote_path: str):
    tansport, sftp = await run_in_threadpool(create_sftp_client)
    with tansport, sftp:
        # Create a remote file object on the SFTP server
        with sftp.open(remote_path, "wb") as remote_file:
            remote_file.set_pipelined()

            # Set up the streaming form data parser
            parser = StreamingFormDataParser(headers=request.headers)
            parser.register("file", MyTarget(remote_file))

            # Iterate through the async generator and parse the multipart form data
            async for chunk in request.stream():
                await run_in_threadpool(parser.data_received, chunk)

        return {"status": "success", "remote_path": remote_path}


@app.get("/test_cocurency")
async def test_cocurency():
    return {"status": "success"}


@app.get("/list_files")
def list_files(path: str = "/"):
    sftp = create_sftp_client()
    files = sftp.listdir(path)
    sftp.close()
    return {"files": files}

@app.post("/copy_file")
def copy_file(source: str, destination: str):
    sftp = create_sftp_client()
    sftp.put(source, destination)
    sftp.close()
    return {"status": "success", "source": source, "destination": destination}

def file_generator(sftp, remote_path):
    print(f'remote_path {remote_path}')
    with sftp.open(remote_path, "rb") as remote_file:
        print(f'open remote_path {remote_path}')
        # remote_file.set_pipelined()
        # yield from remote_file
        # for chunk in iter(lambda: remote_file.read(8192), b""):
            # yield chunk
        while True:
            chunk = remote_file.read(4*1024)
            yield chunk
            if len(chunk) < 4*1024:
                break

@app.get("/download_file")
def download_file(remote_path: str, local_path: str):
    transport, sftp = create_sftp_client()

    # Wrap the remote file object as a generator
    file_gen = file_generator(sftp, remote_path)
    def iterfile(transport, sftp):
        with transport, sftp:
            print(f'opening {remote_path}')
            with sftp.open(remote_path, "rb") as remote_file:
                print(f'open {remote_path}')
                remote_file.set_pipelined()
                while True:
                    chunk = remote_file.read(32768)
                    print(len(chunk), 'chunk')
                    yield chunk
                    if len(chunk) < 32768:
                        break

    # Create a streaming response to send the downloaded data
    response = StreamingResponse(iterfile(transport, sftp), media_type="application/octet-stream")
    response.headers["Content-Disposition"] = f"attachment; filename={local_path}"
    
    return response

if __name__ == '__main__':
    import shutil
    transport, sftp = create_sftp_client()
    with transport, sftp:
        remote_path = 'Cursor.zip'
        # sftp.get(remote_path, remote_path)
        with sftp.open(remote_path, "rb") as remote_file, open('Cursor.zip', 'w+b') as f:
            remote_file.set_pipelined()
            shutil.copyfileobj(remote_file, f, length=32768)
