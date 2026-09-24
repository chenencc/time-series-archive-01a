"""Restore opaque encrypted objects to the original minute Parquet tree."""
from __future__ import annotations

import argparse
import getpass
import hashlib
import json
from pathlib import Path

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes

HERE = Path(__file__).resolve().parent


def open_blob(aes: AESGCM, blob: bytes, associated: bytes) -> bytes:
    if not blob.startswith(b"DARC1\x00"):
        raise ValueError("Unknown object format")
    nonce = blob[6:18]
    return aes.decrypt(nonce, blob[18:], associated)


def main() -> None:
    parser = argparse.ArgumentParser(description="Restore and verify encrypted archive files")
    parser.add_argument("--readme-only", action="store_true", help="Decrypt detailed README without restoring the data")
    args = parser.parse_args()
    params = json.loads((HERE / "parameters.json").read_text(encoding="utf-8"))
    password = getpass.getpass("Archive password: ")
    key = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32,
        salt=bytes.fromhex(params["salt_hex"]), iterations=params["iterations"]).derive(password.encode("utf-8"))
    aes = AESGCM(key)
    manifest = json.loads(open_blob(aes, (HERE / "index.bin").read_bytes(), b"index.bin"))
    output = HERE / "restored"
    if args.readme_only:
        output.mkdir(parents=True, exist_ok=True)
        (output / "README.md").write_text(manifest["readme"], encoding="utf-8")
        print(f"Decrypted detailed README to {output / 'README.md'}")
        return
    for number, item in enumerate(manifest["files"], 1):
        relative = Path(item["relative_path"])
        if relative.is_absolute() or ".." in relative.parts:
            raise ValueError("Unsafe path in index")
        raw = open_blob(aes, (HERE / "objects" / item["object"]).read_bytes(), item["object"].encode("ascii"))
        if len(raw) != item["size"] or hashlib.sha256(raw).hexdigest() != item["sha256"]:
            raise ValueError(f"Hash mismatch at object {number}")
        destination = output / "minute" / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(raw)
        if number % 100 == 0:
            print(f"Restored {number}/{len(manifest['files'])}", flush=True)
    (output / "README.md").write_text(manifest["readme"], encoding="utf-8")
    print(f"Restored {len(manifest['files'])} verified files to {output}")


if __name__ == "__main__":
    main()
