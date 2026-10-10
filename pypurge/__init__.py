import os
import re
import logging
from datetime import datetime, timedelta
from pathlib import Path
from pypurge.version import __version__  # noqa: F401


def purge(directory: str, regex: str, time_span: str, dry_run: bool = True):
    """
    Delete files in a directory (and subdirectories) based on a regex match 
    and their creation time being older than the given relative time span.

    :param directory: The path to the directory to scan.
    :param regex: A regex pattern to match file names.
    :param time_span: A relative time span string (e.g., "3D", "4W", "6M", "7Y").
    :param dry_run: If True, simulate deletions without actually deleting files.
    """
    # Convert time_span to a timedelta
    unit_mapping = {"D": "days", "W": "weeks", "M": "months", "Y": "years"}
    if time_span[-1] not in unit_mapping:
        raise ValueError(f"Invalid time span unit. Use one of {list(unit_mapping.keys())}.")

    value = int(time_span[:-1])
    unit = unit_mapping[time_span[-1]]

    if unit == "days":
        delta = timedelta(days=value)
    elif unit == "weeks":
        delta = timedelta(weeks=value)
    elif unit == "months":
        delta = timedelta(days=value * 30)  # Approximation
    elif unit == "years":
        delta = timedelta(days=value * 365)  # Approximation

    cutoff_time = datetime.now() - delta
    pattern = re.compile(regex)

    root_dir = Path(directory)
    deleted = set()  # Files deleted (or that would be deleted in dry run)
    removed_dirs = set()  # Directories removed (or that would be removed in dry run)

    # Bottom-up walk so that a directory is examined after its children
    for root, _, files in os.walk(directory, topdown=False):
        for file in files:
            file_path = Path(root) / file
            try:
                # Match file name with regex
                if not pattern.match(file):
                    continue

                # Get file creation time
                creation_time = datetime.fromtimestamp(file_path.stat().st_mtime)

                # Check if the file is older than the cutoff time
                if creation_time < cutoff_time:
                    deleted.add(file_path)
                    if dry_run:
                        logging.info(f"[DRY RUN] Would delete: {file_path}")
                    else:
                        logging.info(f"Deleting: {file_path}")
                        file_path.unlink()
            except Exception as e:
                logging.error(f"Error processing file {file_path}: {e}")
                raise e

        # Remove the directory if the purge left it empty (never the root directory)
        dir_path = Path(root)
        if dir_path == root_dir:
            continue
        try:
            remaining = [
                entry for entry in dir_path.iterdir()
                if entry not in deleted and entry not in removed_dirs
            ]
            if remaining:
                continue
            # Directories that were already empty are only removed after a grace period,
            # in case a writer (camera, FTP upload) has just created them.
            touched = any(d.parent == dir_path for d in deleted | removed_dirs)
            if not touched and datetime.fromtimestamp(dir_path.stat().st_mtime) > datetime.now() - timedelta(days=1):
                continue
            removed_dirs.add(dir_path)
            if dry_run:
                logging.info(f"[DRY RUN] Would remove empty directory: {dir_path}")
            else:
                logging.info(f"Removing empty directory: {dir_path}")
                dir_path.rmdir()
        except Exception as e:
            logging.error(f"Error processing directory {dir_path}: {e}")
            raise e
