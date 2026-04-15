import os

import aiofiles

from app.utils.hashing import sha256_hex


class CASService:
    def __init__(self, root: str) -> None:
        self.root = root

    def _path(self, sha256: str) -> str:
        return os.path.join(self.root, sha256[:2], sha256[2:4], sha256)

    async def exists(self, sha256: str) -> bool:
        return os.path.exists(self._path(sha256))

    async def write(self, data: bytes, sha256: str) -> str:
        """Write bytes to CAS. Returns relative cas_path. Idempotent."""
        path = self._path(sha256)
        if not os.path.exists(path):
            os.makedirs(os.path.dirname(path), exist_ok=True)
            async with aiofiles.open(path, "wb") as f:
                await f.write(data)
        return os.path.relpath(path, self.root)

    async def read(self, sha256: str) -> bytes:
        path = self._path(sha256)
        async with aiofiles.open(path, "rb") as f:
            return await f.read()

    def get_absolute_path(self, sha256: str) -> str:
        return self._path(sha256)
