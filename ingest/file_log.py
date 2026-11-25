"""Her indirilen dosyanin parmak izini (SHA-256) tutan kayit defteri."""

import csv
import hashlib
from datetime import datetime, timezone
from pathlib import Path

FIELDS = ["file_name", "custodian", "business_date", "sha256", "size_bytes",
          "received_at_utc", "status"]


def sha256_of(path: Path) -> str:
    """Dosyanin parmak izi. Icerik ayniysa parmak izi de aynidir."""
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def already_processed(log_path: Path, digest: str) -> bool:
    """Bu parmak izi daha once kaydedildi mi?"""
    if not log_path.exists():
        return False
    with log_path.open(newline="", encoding="utf-8") as f:
        return any(row["sha256"] == digest for row in csv.DictReader(f))


def record(log_path: Path, file_path: Path, custodian: str, business_date: str,
           digest: str, status: str = "downloaded") -> None:
    """Deftere yeni bir satir ekle."""
    is_new = not log_path.exists()
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        if is_new:
            w.writeheader()
        w.writerow({
            "file_name": file_path.name,
            "custodian": custodian,
            "business_date": business_date,
            "sha256": digest,
            "size_bytes": file_path.stat().st_size,
            "received_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "status": status,
        })
