import asyncio
import asyncssh, sys
import os

async def run_client() -> None:
    async with asyncssh.connect(os.environ.get('SFTP_SERVER'), 1443, password='tiger', username='testuser', known_hosts=None) as conn:
        async with conn.start_sftp_client() as sftp:
            await sftp.put('CascadiaCode-2111.01.zip')

try:
    asyncio.get_event_loop().run_until_complete(run_client())
except (OSError, asyncssh.Error) as exc:
    sys.exit('SFTP operation failed: ' + str(exc))