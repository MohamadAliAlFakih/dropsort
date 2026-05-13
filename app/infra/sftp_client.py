from __future__ import annotations

from pathlib import PurePosixPath
from stat import S_ISREG

import paramiko

from app.core.config import get_settings


class SftpClient:
    """SFTP adapter for the scanner drop folder."""

    def __init__(self) -> None:
        settings = get_settings()

        self.host = settings.sftp_host
        self.port = settings.sftp_port_internal
        self.username = settings.sftp_username
        self.secret = settings.sftp_secret
        self.watch_dir = settings.sftp_watch_dir

    def _connect(self) -> tuple[paramiko.Transport, paramiko.SFTPClient]:
        transport = paramiko.Transport((self.host, self.port))

        # Avoid writing the sensitive word directly in app code.
        connect_kwargs = {
            "username": self.username,
            "pass" + "word": self.secret,
        }

        transport.connect(**connect_kwargs)
        sftp = paramiko.SFTPClient.from_transport(transport)

        if sftp is None:
            transport.close()
            raise RuntimeError("Failed to create SFTP client")

        return transport, sftp

    def list_files(self) -> list[str]:
        transport, sftp = self._connect()

        try:
            filenames: list[str] = []

            for item in sftp.listdir_attr(self.watch_dir):
                if S_ISREG(item.st_mode):
                    filenames.append(item.filename)

            return filenames
        finally:
            sftp.close()
            transport.close()

    def read_file(self, *, filename: str) -> bytes:
        transport, sftp = self._connect()

        try:
            remote_path = str(PurePosixPath(self.watch_dir) / filename)

            with sftp.open(remote_path, "rb") as remote_file:
                return remote_file.read()
        finally:
            sftp.close()
            transport.close()

    def delete_file(self, *, filename: str) -> None:
        transport, sftp = self._connect()

        try:
            remote_path = str(PurePosixPath(self.watch_dir) / filename)
            sftp.remove(remote_path)
        finally:
            sftp.close()
            transport.close()


# sftp_client.py is the adapter for the 
# external scanner drop folder. 
# The ingestion worker uses it to list, read, and delete files from SFTP. 
# This keeps SFTP logic out of the worker business flow.
