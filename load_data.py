"""
load_data.py - REPLACED.

The first version of this script imported a hand-made CSV into a simple
'groundwater' table. JalMitra now uses the verified official database built
from the CGWB PDFs (see README.md). The old script is kept in
backup/app_v1_20261122/load_data.py.

To (re)build the official database, run from the JalMitra folder:

    python build_dataset.py       # read the PDFs in data/raw -> checked CSV files
    python build_database.py      # CSV files -> data/groundwater.db
    python validate_database.py   # acceptance tests -> data/validation_report.csv

This script does nothing else, so it can never overwrite the database by mistake.
"""

if __name__ == "__main__":
    print(__doc__)
