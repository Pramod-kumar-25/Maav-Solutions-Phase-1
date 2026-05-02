import os
import aiofiles
from pathlib import Path

class FileStorageService:
    """
    Simple Local Filesystem Storage Service.
    Phase 1 Implementation.
    """
    def __init__(self, storage_root: str = "storage"):
        self.storage_root = Path(storage_root)
        self.storage_root.mkdir(parents=True, exist_ok=True)

    async def write_blob(self, relative_path: str, data: bytes) -> str:
        """
        Write binary data to local filesystem.
        Returns the absolute path (or stored path).
        """
        full_path = self.storage_root / relative_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        
        async with aiofiles.open(full_path, 'wb') as f:
            await f.write(data)
            
        return str(full_path)
