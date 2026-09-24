"""Restore and verify the separately published encrypted tick snapshot."""
from __future__ import annotations

import argparse
import getpass
import hashlib
import io
import json
import zipfile
from pathlib import Path, PurePosixPath

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes

HERE = Path(__file__).resolve().parent
ASSETS = HERE / "tick_assets"


def open_blob(aes: AESGCM, blob: bytes, associated: bytes) -> bytes:
    if not blob.startswith(b"DARC1\x00"):
        raise ValueError("Unknown object format")
    return aes.decrypt(blob[6:18], blob[18:], associated)


def main() -> None:
    parser = argparse.ArgumentParser(description="Restore encrypted five-level order-book files")
    parser.add_argument("--readme-only", action="store_true", help="Decrypt dataset notes only")
    args = parser.parse_args()
    params = json.loads((ASSETS / "tick-parameters.json").read_text(encoding="utf-8"))
    password = getpass.getpass("Archive password: ")
    key = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32,
        salt=bytes.fromhex(params["salt_hex"]), iterations=params["iterations"]).derive(password.encode("utf-8"))
    aes = AESGCM(key)
    index = json.loads(open_blob(aes, (ASSETS / "tick-index.bin").read_bytes(), b"tick-index.bin"))
    output = HERE / "restored" / "tick"
    if args.readme_only:
        output.mkdir(parents=True, exist_ok=True)
        (output / "README.md").write_text(index["readme"], encoding="utf-8")
        print(f"Decrypted dataset notes to {output / 'README.md'}")
        return

    seen: set[str] = set()
    for number, shard in enumerate(index["shards"], 1):
        encrypted = (ASSETS / shard["object"]).read_bytes()
        archive_bytes = open_blob(aes, encrypted, shard["object"].encode("ascii"))
        if len(archive_bytes) != shard["archive_size"] or hashlib.sha256(archive_bytes).hexdigest() != shard["archive_sha256"]:
            raise ValueError(f"Encrypted archive hash mismatch at shard {number}")
        with zipfile.ZipFile(io.BytesIO(archive_bytes)) as archive:
            names = set(archive.namelist())
            expected = {item["relative_path"] for item in shard["files"]}
            if names != expected:
                raise ValueError(f"Archive contents do not match index at shard {number}")
            for item in shard["files"]:
                relative = PurePosixPath(item["relative_path"])
                if relative.is_absolute() or ".." in relative.parts or item["relative_path"] in seen:
                    raise ValueError("Unsafe or repeated path in index")
                raw = archive.read(item["relative_path"])
                if len(raw) != item["size"] or hashlib.sha256(raw).hexdigest() != item["sha256"]:
                    raise ValueError(f"SHA-256 mismatch for file {number}")
                destination = output.joinpath(*relative.parts)
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_bytes(raw)
                seen.add(item["relative_path"])
        if number % 5 == 0:
            print(f"Restored {number}/{len(index['shards'])} archives", flush=True)
    if len(seen) != index["file_count"]:
        raise ValueError(f"Expected {index['file_count']} daily files; restored {len(seen)}")
    (output / "README.md").write_text(index["readme"], encoding="utf-8")
    print(f"Restored and verified {len(seen)} daily files to {output}")


if __name__ == "__main__":
    main()
