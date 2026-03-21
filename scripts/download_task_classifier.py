"""
Download the HuggingFace model snapshot into a local folder (so ETL can ship it).

Usage (PowerShell):
  python scripts/download_task_classifier.py ^
    --model "MoritzLaurer/DeBERTa-v3-large-mnli-fever-anli-ling-wanli" ^
    --out_dir "models/task_classification/hf_model"
"""

from __future__ import annotations

import argparse
import os
import shutil


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--model", required=True, help="HuggingFace model id (e.g. facebook/bart-large-mnli)")
    p.add_argument("--out_dir", required=True, help="Directory to place the snapshot (will be overwritten)")
    args = p.parse_args()

    try:
        from huggingface_hub import snapshot_download  # type: ignore
    except Exception as e:
        raise SystemExit(
            "huggingface-hub is not installed. Install it first, e.g. `pip install huggingface-hub`."
        ) from e

    out_dir = os.path.abspath(args.out_dir)
    if os.path.exists(out_dir):
        shutil.rmtree(out_dir)
    os.makedirs(out_dir, exist_ok=True)

    local_dir = snapshot_download(repo_id=args.model, local_dir=out_dir, local_dir_use_symlinks=False)
    print(f"Downloaded {args.model} -> {local_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())









