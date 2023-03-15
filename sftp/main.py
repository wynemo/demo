import paramiko
import os

transport = paramiko.Transport((os.environ.get('SFTP_SERVER'),1443))

# automatically add the host key for non-interactive authentication

# connect to the server
transport.connect(None, username='testuser', password='tiger')

# create an SFTP client
sftp = paramiko.SFTPClient.from_transport(transport)

# create a stream-like object (in this example, we're using BytesIO)
from io import BytesIO
data = b'Hello, world!'
stream = BytesIO(data)

# upload the stream to the server
with open('/Users/tommygreen/Downloads/CascadiaCode-2111.01.zip', 'rb') as f:
    sftp.putfo(f, 'CascadiaCode-2111.01.zip')

# close the SFTP session and SSH connection
sftp.close()
transport.close()