#!/usr/bin/python3

import hashlib
import shutil
import subprocess
import sys
from pathlib import Path


MOD_DIR = Path("mod")
MODFILELIST_PATH = MOD_DIR.joinpath("modfilelist.txt")
MOD_FILES_PATH = Path("mod_files.txt")
MOD_REVCOUNT_PATH = Path("mod_revcount.txt")


def main() -> int:
    # remove old folder
    if MOD_DIR.is_dir():
        shutil.rmtree(MOD_DIR, ignore_errors=True)

    md5s = {}
    with open(MOD_FILES_PATH, "r") as f:
        lines = f.readlines()

        for line in lines:
            # stupid newlines
            line = line.strip("\r\n")

            # ignore empty lines and comment lines
            if line == "" or line.startswith("#"):
                continue

            # copy to mod folder
            line_path = MOD_DIR.joinpath(line)
            line_path.resolve().parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(line, line_path)

            # add md5 to dict
            data = line_path.read_bytes()
            md5 = hashlib.md5(data).hexdigest()
            md5s[line] = md5

    # find revision number
    revision = 1
    if MOD_REVCOUNT_PATH.is_file():
        with open(MOD_REVCOUNT_PATH, "r") as f:
            revision = int(f.readline()) + 1
    
    # save revision number
    with open(MOD_REVCOUNT_PATH, "w") as f:
        f.write(f"{revision}\n")

    # write filelist
    with open("mod/modfilelist.txt", "w") as f:
        f.write(f"{revision}\n")
        for filename, md5 in md5s.items():
            f.write(f"{filename} {md5}\n")

    print(f"Updated mod to revision {revision}.")
    print(f"Press CTRL+C to skip upload.")
    subprocess.run("scp -r mod ddm@runciman.hacksoc.org:~/private_html", stdout=sys.stdout, stderr=sys.stderr)

    return 0


if __name__ == "__main__":
    sys.exit(main())
