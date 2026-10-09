"""Upload the case dataset to LangSmith (also: make upload-dataset).

Usage:
    python -m evals.upload_dataset [--name NAME] [--force]

The dataset is frozen between eval runs; --force replaces an existing dataset of the
same name and should only be used when the fixtures have intentionally changed.
"""

import argparse
import sys


def main() -> int:
    from src import config  # noqa: F401  (loads .env)

    from evals.dataset import DATASET_NAME, upload

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--name", default=DATASET_NAME)
    parser.add_argument(
        "--force",
        action="store_true",
        help="replace an existing dataset of the same name (breaks freeze)",
    )
    args = parser.parse_args()
    print(upload(args.name, force=args.force))
    return 0


if __name__ == "__main__":
    sys.exit(main())
