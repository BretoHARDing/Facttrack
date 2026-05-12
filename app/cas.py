import hashlib
from pathlib import Path
class LocalCAS:
    def __init__(self, base_dir: str = "./cas_store"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
    def _path_for_hash(self, h: str) -> Path: return self.base_dir / h[:2] / h[2:4] / h
    async def store(self, data: bytes) -> str:
        h = hashlib.sha256(data).hexdigest()
        p = self._path_for_hash(h)
        if p.exists(): return h
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(data)
        return h
    async def read(self, h: str) -> bytes:
        p = self._path_for_hash(h)
        if not p.exists(): raise FileNotFoundError(f"CAS miss: {h}")
        data = p.read_bytes()
        if hashlib.sha256(data).hexdigest() != h: raise ValueError("CAS integrity violation")
        return data
cas_store = LocalCAS()
