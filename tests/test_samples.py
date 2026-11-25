import csv
import json
from xml.etree import ElementTree as ET

import pytest

from scripts.generate_samples import OUT, STAMP, main


@pytest.fixture(scope="module", autouse=True)
def generate_files():
    main()  # testlerden once dosyalari uret


def test_ubs_csv_has_expected_columns():
    with (OUT / "ubs" / f"UBS_POS_{STAMP}.csv").open(encoding="utf-8") as f:
        header = next(csv.reader(f, delimiter=";"))
    assert header == ["account_id", "isin", "quantity", "price", "currency", "business_date"]


def test_jb_trailer_matches_detail_count():
    lines = (OUT / "jb" / f"JB_POS_{STAMP}.txt").read_text(encoding="ascii").splitlines()
    details = [line for line in lines if line.startswith("D")]
    assert lines[-1].startswith("T")
    assert int(lines[-1][1:]) == len(details)


def test_jb_detail_lines_are_58_characters():
    lines = (OUT / "jb" / f"JB_POS_{STAMP}.txt").read_text(encoding="ascii").splitlines()
    assert all(len(line) == 58 for line in lines if line.startswith("D"))


def test_pictet_summary_matches_positions():
    root = ET.parse(OUT / "pictet" / f"PICTET_POS_{STAMP}.xml").getroot()
    count = int(root.find("Summary").get("positionCount"))
    assert count == len(root.findall(".//Position"))


def test_prices_json_has_px_last_for_every_security():
    data = json.loads((OUT / "market" / f"prices_{STAMP}.json").read_text(encoding="utf-8"))
    assert all("px_last" in s for s in data["securities"])


def test_every_bank_file_has_done_marker():
    for folder, prefix in [("ubs", "UBS"), ("jb", "JB"), ("pictet", "PICTET")]:
        assert (OUT / folder / f"{prefix}_POS_{STAMP}.done").exists()
