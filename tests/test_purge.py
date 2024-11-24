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
