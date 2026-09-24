# Archived market time-series files

The repository's Git LFS archive contains about one year of minute bars. A separate encrypted snapshot of native five-level order-book data is stored in the `ticks/` folder.

```bash
git clone https://github.com/chenencc/time-series-archive-01a.git
cd time-series-archive-01a
git lfs pull
python -m pip install cryptography
python restore.py
```

The restore script prompts for a password. It verifies each restored file with SHA-256 and writes the files and their detailed README to `restored/`.
To read the detailed README first, run `python restore.py --readme-only`.

## Five-level order-book snapshot

After `git lfs pull` has downloaded the repository data, the order-book files are already in `ticks/`. Run:

```bash
python tick_restore.py
```

This restores the original daily QMT tick files under `restored/tick/` and verifies every file with SHA-256. To decrypt only the order-book dataset notes, run `python tick_restore.py --readme-only`.

The password is not stored here. Access to this public repository does not imply confidentiality: a short password can be guessed offline.


