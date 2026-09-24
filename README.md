# Archived time-series files

The objects and detailed documentation are encrypted. This repository uses Git LFS.

```bash
git clone https://github.com/chenencc/time-series-archive-01a.git
cd time-series-archive-01a
git lfs pull
python -m pip install cryptography
python restore.py
```

The restore script prompts for a password. It verifies each restored file with SHA-256 and writes the files and their detailed README to `restored/`.
To read the detailed README first, run `python restore.py --readme-only`.

The password is not stored here. Access to this public repository does not imply confidentiality: a short password can be guessed offline.


