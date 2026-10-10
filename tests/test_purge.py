import pypurge
from pathlib import Path
import os
import shutil
import datetime
import pytest


@pytest.fixture
def setup_teardown():

    # Setup code
    # Create a tmp directory with some files
    os.makedirs("tests/data", exist_ok=True)
    for i in range(1, 6):
        with open(f"tests/data/file{i}.txt", "w") as f:
            f.write("test")
        # Set creation time to i days ago
        creation_time = datetime.datetime.now() - datetime.timedelta(days=i)
        os.utime(f"tests/data/file{i}.txt", (creation_time.timestamp(), creation_time.timestamp()))

    yield  # Code after `yield` runs after the test

    # Teardown code
    # Clean up
    shutil.rmtree("tests/data")


def test_purge(setup_teardown):

    # Test invalid time spa
    try:
        pypurge.purge("tests/data", r"file\d.txt", "1X", dry_run=True)
    except ValueError:
        pass
    else:
        raise AssertionError("ValueError not raised")

    # Test dry run
    pypurge.purge("tests/data", r"file\d.txt", "3D", dry_run=True)
    assert Path("tests/data/file1.txt").exists()
    assert Path("tests/data/file2.txt").exists()
    assert Path("tests/data/file3.txt").exists()
    assert Path("tests/data/file4.txt").exists()
    assert Path("tests/data/file5.txt").exists()

    # Test real deletion
    pypurge.purge("tests/data", r"file\d.txt", "3D", dry_run=False)
    assert Path("tests/data/file1.txt").exists()
    assert Path("tests/data/file2.txt").exists()
    assert not Path("tests/data/file3.txt").exists()
    assert not Path("tests/data/file4.txt").exists()
    assert not Path("tests/data/file5.txt").exists()


def test_purge_removes_empty_directories():
    base = Path("tests/data_dirs")
    try:
        old = datetime.datetime.now() - datetime.timedelta(days=10)
        (base / "a" / "b").mkdir(parents=True)
        (base / "keep").mkdir(parents=True)
        (base / "a" / "b" / "old.txt").write_text("x")
        os.utime(base / "a" / "b" / "old.txt", (old.timestamp(), old.timestamp()))
        (base / "keep" / "new.txt").write_text("x")
        (base / "empty_recent").mkdir()

        # Dry run changes nothing
        pypurge.purge(str(base), r".*\.txt$", "3D", dry_run=True)
        assert (base / "a" / "b" / "old.txt").exists()

        pypurge.purge(str(base), r".*\.txt$", "3D", dry_run=False)
        assert not (base / "a").exists()  # emptied directories removed bottom-up
        assert (base / "keep" / "new.txt").exists()
        assert (base / "empty_recent").exists()  # grace period
        assert base.exists()  # root is never removed
    finally:
        shutil.rmtree(base, ignore_errors=True)
