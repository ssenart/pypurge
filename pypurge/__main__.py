import argparse
import sys
import pypurge
import traceback
import logging


def main() -> int:
    """Main function"""
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--version",
                        action="version",
                        version=f"purge {pypurge.__version__}")
    parser.add_argument("-d", "--directory",
                        required=True,
                        help="Root directory to purge")
    parser.add_argument("-r", "--regex",
                        required=True,
                        help="Regex pattern to match files")
    parser.add_argument("-t", "--time-span",
                        required=True,
                        help="Relative time span (e.g., '3D', '4W', '6M', '7Y')")
    parser.add_argument("--no-dry-run",
                        action="store_true",
                        help="Delete files for real")

    args = parser.parse_args()

    if args.no_dry_run:
        logging.info("Real deletion mode activated.")
    else:
        print("Dry run mode. No files will be deleted.")

    try:
        pypurge.purge(args.directory, args.regex, args.time_span, not args.no_dry_run)

        logging.info("Purge completed successfully.")
    except BaseException:
        logging.error('An error occured: %s', traceback.format_exc())
        return 1

    return 0


if __name__ == '__main__':
    sys.exit(main())
