"""
Usage: python fetch_one.py <project_slug>

The script fetches one project from Github, checking out the buggy commit,
and then patches it with the essential information for it to be buildable.
The project is specified with the Project Slug that contains project name,
CVE ID, and version tag.

Example:

``` bash
$ python3 fetch_one.py apache__camel_CVE-2018-8041_2.20.3
```
"""

import os
import argparse
import csv
import subprocess
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
from src.config import DATA_DIR

if __name__ == "__main__":
  parser = argparse.ArgumentParser()
  parser.add_argument("project_slug", type=str)
  args = parser.parse_args()

  project_slug = args.project_slug
  reader = csv.reader(open(f"{DATA_DIR}/project_info.csv"))
  for line in reader:
    if line[1] == project_slug:
      row = line

  repo_url = row[8]
  commit_id = row[10]
  target_dir = f"{DATA_DIR}/project-sources/{project_slug}"

  if os.path.exists(f"{DATA_DIR}/project-sources/{project_slug}"):
    print(f">> [fetch_one] skipping")
    exit(0)

  print(f">> [fetch_one] Cloning repository from `{repo_url}`...")
  git_clone_cmd = ["git", "clone", "--depth", "1", repo_url, target_dir]
  subprocess.run(git_clone_cmd)

  print(f">> [fetch_one] Fetching and checking out commit `{commit_id}`...")
  git_fetch_commit = ["git", "fetch", "--depth", "1", "origin", commit_id]
  subprocess.run(git_fetch_commit, cwd=target_dir)
  git_checkout_commit = ["git", "checkout", commit_id]
  subprocess.run(git_checkout_commit, cwd=target_dir)

  patch_dir = f"{DATA_DIR}/patches/{project_slug}.patch"
  if os.path.exists(patch_dir):
    print(f">> [fetch_one] Applying patch `{patch_dir}`...")
    git_patch = ["git", "apply", patch_dir]
    subprocess.run(git_patch, cwd=target_dir)
  else:
    print(f">> [fetch_one] There is no patch; skipping patching the repository")
