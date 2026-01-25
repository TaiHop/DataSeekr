# cleanup_csvs.py
import os
import glob
import time

# Wait 6..7 seconds before cleaning up
time.sleep(5)


def cleanup_csvs(folder: str = "."):
    """
    Remove all CSV files in the given folder.
    Default is current folder (project folder in VS Code).
    """
    csv_files = glob.glob(os.path.join(folder, "*.csv"))
    if not csv_files:
        print("No CSV files found to delete.")
        return

    for f in csv_files:
        try:
            os.remove(f)
            print(f"🗑 Deleted: {f}")
        except Exception as e:
            print(f"⚠ Failed to delete {f}: {e}")


# Run cleanup in project folder
cleanup_csvs()
