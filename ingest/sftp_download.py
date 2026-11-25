"""Bankanin SFTP sunucusundan gunluk pozisyon dosyasini indirir."""

import argparse
from pathlib import Path

import paramiko

from ingest.file_log import already_processed, record, sha256_of

BANKS = {
    "ubs": {"host": "127.0.0.1", "port": 2222, "user": "ubs", "remote_dir": "outbound",
            "prefix": "UBS_POS", "ext": "csv"},
}
KEY = Path("secrets/bank_sftp_key")
RAW = Path("data/raw")
FILE_LOG = RAW / "file_log.csv"


class FileNotReady(Exception):
    """Banka dosyayi henuz bitirmedi (.done yok)."""


def download(bank: str, business_date: str) -> Path:
    cfg = BANKS[bank]
    stamp = business_date.replace("-", "")
    data_name = f"{cfg['prefix']}_{stamp}.{cfg['ext']}"
    done_name = f"{cfg['prefix']}_{stamp}.done"

    client = paramiko.SSHClient()
    client.load_system_host_keys()                                # 2: bankanin kimligi kayitli mi?
    client.set_missing_host_key_policy(paramiko.RejectPolicy())  # tanimiyorsan baglanma
    client.connect(cfg["host"], port=cfg["port"], username=cfg["user"],  # 1 + 3-4: baglan,
                   key_filename=str(KEY), look_for_keys=False, allow_agent=False)  # anahtarla gir
    try:
        sftp = client.open_sftp()
        names = sftp.listdir(cfg["remote_dir"])                   # 5-6: klasorde ne var?
        if done_name not in names:                                # .done yoksa dokunma
            raise FileNotReady(f"{bank}: {done_name} yok, banka henuz bitirmedi")
        landing = RAW / bank / business_date
        landing.mkdir(parents=True, exist_ok=True)
        local = landing / data_name
        sftp.get(f"{cfg['remote_dir']}/{data_name}", str(local))  # 7-8: dosyayi al
    finally:
        client.close()                                            # 9: kapat

    digest = sha256_of(local)                                     # parmak izi
    if already_processed(FILE_LOG, digest):
        print(f"{data_name}: ayni dosya daha once islendi, atlaniyor")
        return local
    record(FILE_LOG, local, bank, business_date, digest)          # deftere yaz
    print(f"{data_name}: indirildi -> {local} (sha256 {digest[:12]}...)")
    return local


def main():
    parser = argparse.ArgumentParser(description="Banka SFTP indirici")
    parser.add_argument("--bank", required=True, choices=sorted(BANKS))
    parser.add_argument("--date", required=True, help="YYYY-MM-DD")
    args = parser.parse_args()
    download(args.bank, args.date)


if __name__ == "__main__":
    main()
