import os

import paramiko
from fastapi import FastAPI
from fastapi.concurrency import run_in_threadpool
from starlette.requests import Request
from streaming_form_data import StreamingFormDataParser
from streaming_form_data.targets import BaseTarget

app = FastAPI()

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
