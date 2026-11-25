from ingest.file_log import already_processed, record, sha256_of


def test_same_content_gives_same_fingerprint(tmp_path):
    a = tmp_path / "a.csv"
    b = tmp_path / "b.csv"
    a.write_text("A001;US0378331005;81,00\n")
    b.write_text("A001;US0378331005;81,00\n")
    assert sha256_of(a) == sha256_of(b)


def test_one_character_changes_the_fingerprint(tmp_path):
    a = tmp_path / "a.csv"
    b = tmp_path / "b.csv"
    a.write_text("A001;US0378331005;81,00\n")
    b.write_text("A001;US0378331005;82,00\n")
    assert sha256_of(a) != sha256_of(b)


def test_duplicate_file_is_detected(tmp_path):
    log = tmp_path / "file_log.csv"
    f = tmp_path / "UBS_POS_20261124.csv"
    f.write_text("A001;US0378331005;81,00\n")
    digest = sha256_of(f)
    assert not already_processed(log, digest)
    record(log, f, "ubs", "2026-11-24", digest)
    assert already_processed(log, digest)
