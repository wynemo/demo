## setup server

    git clone https://github.com/pkg/sftp.git
    cd /tmp/sftp/examples/go-sftp-server
    ssh-keygen
    go run main.go

## run local http server

    pdm run uvicorn new_http_sftp:app

## test file upload

    curl -F 'file=@/path/to/your/file.zip' http://127.0.0.1:8000/upload_file?remote_path=Cursor.zip
