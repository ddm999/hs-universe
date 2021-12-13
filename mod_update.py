#!/usr/bin/python3

from __future__ import annotations

import argparse
import hashlib
import os
import shutil
import ssl
import stat
import sys
import urllib.request
import logging as log
from pathlib import Path

BASEURL = "https://runciman.hacksoc.org/~/ddm/mod/"
FILELIST = BASEURL+"modfilelist.txt"
VERBOSITY = log.INFO
FORCE = False
SKIPREV = False
NOMOD = False
MODFILELIST_PATH = Path("modfilelist.txt")
BACKUP_DIR = Path("bak/")


log.basicConfig(
    format="[%(levelname)s] %(message)s",
    level=VERBOSITY,
    stream=sys.stdout
)


# funny globals go brrr
sslcontext = ssl.create_default_context()
sslcontext.check_hostname = False
sslcontext.verify_mode = ssl.VerifyMode.CERT_NONE


def main() -> int:
    if MODFILELIST_PATH.is_file():
        with open(MODFILELIST_PATH, "r") as f:
            local_lines = f.readlines()
    else:
        log.debug("No local modfilelist, setting revision to 0.")
        local_lines = ["0", ""]

    ret = urllib.request.urlopen(FILELIST, context=sslcontext)
    net_lines: list[str] = [line+"\n" for line in ret.read().decode("utf-8").split("\n")]

    local_rev = int(local_lines[0].strip("\r\n"))
    net_rev = int(net_lines[0].strip("\r\n"))
    if net_rev > local_rev or SKIPREV:
        print(f"Found mod update (revision {local_rev} -> {net_rev}).")
        if NOMOD is False:
            with open("modfilelist.txt", "w") as f:
                f.writelines(net_lines)
        else:
            log.info("Update will not be saved as --nomod is set.")
        update(net_lines[1:])
        return 0

    print(f"Mod is up to date (revision {local_rev}).")
    return 0


def update(filelines: str) -> int:
    not_ok = 0
    actually_changed_a_file = False
    for line in filelines:
        line = line.strip("\r\n")
        if line == "" or line.startswith("#"):
            continue

        x = line.split(" ")
        file_path = Path(x[0])
        net_md5 = x[1].strip("\r\n")

        file_backup_path = BACKUP_DIR.joinpath(file_path)
        if (not file_path.parents[0] == "mod") and (not file_backup_path.is_file()):
            # not backed up (and not mod framework), assume original and back it up
            file_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(file_path, file_backup_path)
            log.info(f"Made a backup of {file_path}.")
        else:
            # get local md5
            local_md5 = "file doesn't exist"
            if file_path.is_file():
                data = file_path.read_bytes()
                local_md5 = hashlib.md5(data).hexdigest()

            log.debug(f"MD5 download test: local '{local_md5}' vs net '{net_md5}'.")
            # if md5s match, don't download this file
            if local_md5 == net_md5:
                if FORCE:
                    log.info(f"Forcing redownload of '{file_path}'.")
                else:
                    log.debug(f"'{file_path}' skipped, unchanged from current.")
                    continue

        # file should be downloaded if we get here
        count = 0
        while True:
            ret = urllib.request.urlopen(BASEURL+str(file_path), context=sslcontext)
            data: str = ret.read()
            dl_md5 = hashlib.md5(data).hexdigest()
            log.debug(f"MD5 verify test: downloaded '{dl_md5}' vs net '{net_md5}'.")
            if dl_md5 == net_md5:
                if NOMOD is False:
                    # ensure not read-only (only if exists)
                    if file_path.is_file():
                        perms = stat.S_IMODE(os.lstat(file_path).st_mode)
                        os.chmod(file_path, perms | stat.S_IWRITE)

                    with open(file_path, "wb") as f:
                        f.write(data)
                    log.info(f"'{file_path}' updated.")
                else:
                    log.info(f"--nomod set: '{file_path}' would've been updated.")
                actually_changed_a_file = True
                break
            else:
                count += 1
                log.debug(f"Validity check failed (file: '{file_path}', count: {count}).")
                if count > 3:
                    log.warning(f"Validity check failed for '{file_path}' after 3 attempts.")
                    not_ok = 1
                    break

    if not actually_changed_a_file:
        if NOMOD is False:  # kinda illogical with --nomod set, so ignore this case
            log.warning(f"No files were changed by this update. Either you made the update, or something's gone wrong.")

    return not_ok


def get_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Updates HackSoc Universe."
    )
    parser.add_argument(
        '--info',
        choices=['error', 'e', 'warning', 'w', 'info', 'i', 'verbose', 'v', 'debug', 'd'],
        help="set information level", default='info'
    )
    parser.add_argument(
        '--nomod', action='store_true',
        help="do not modify any files"
    )
    parser.add_argument(
        '--skiprev', action='store_true',
        help="bypass revision number check"
    )
    parser.add_argument(
        '--force', action='store_true',
        help="force redownload all files (implies --skiprev)"
    )

    return parser


def parse():
    global FORCE, SKIPREV, NOMOD, VERBOSITY
    parser = get_parser()
    args = parser.parse_args()
    FORCE = args.force
    SKIPREV = args.skiprev or args.force
    NOMOD = args.nomod
    log_level_mapping = {
        ("error", "e"): log.ERROR,
        ("warning", "w"): log.WARNING,
        ("info", "i"): log.INFO,
        ("debug", "d", "verbose", "v"): log.DEBUG,
    }
    for choice, level in log_level_mapping.items():
        if args.info in choice:
            VERBOSITY = level
            break


if __name__ == "__main__":
    try:
        parse()
        main()
    except Exception as error:
        log.fatal("fuck it broke. press enter to close", exc_info=error)
        input()
    sys.exit()
