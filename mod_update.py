#!/usr/bin/python3

from __future__ import annotations

import argparse
import hashlib
import os
import shutil
import ssl
import stat
import sys
import traceback
import urllib.request
import logging as log

BASEURL = "https://runciman.hacksoc.org/~/ddm/mod/"
FILELIST = BASEURL+"modfilelist.txt"
VERBOSITY = log.INFO
FORCE = False
SKIPREV = False
NOMOD = False


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
    local_lines = []
    if os.path.isfile("modfilelist.txt"):
        with open("modfilelist.txt", "r") as f:
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
        _ = update(net_lines[1:])
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
        filename = x[0]
        net_md5 = x[1].strip("\r\n")

        if (not filename.startswith("mod")) and (not os.path.isfile(f"bak/{filename}")):
            # not backed up (and not mod framework), assume original and back it up
            os.makedirs(os.path.dirname(f"bak/{filename}"), exist_ok=True)
            shutil.copyfile(filename, f"bak/{filename}")
            log.info(f"Made a backup of {filename}.")
        else:
            # get local md5
            local_md5 = "file doesn't exist"
            if os.path.isfile(filename):
                data = open(filename, "rb").read()
                local_md5 = hashlib.md5(data).hexdigest()

            log.debug(f"MD5 download test: local '{local_md5}' vs net '{net_md5}'.")
            # if md5s match, don't download this file
            if local_md5 == net_md5:
                if FORCE:
                    log.info(f"Forcing redownload of {filename}.")
                else:
                    log.debug(f"'{filename}' skipped, unchanged from current.")
                    continue

        # file should be downloaded if we get here
        count = 0
        while True:
            ret = urllib.request.urlopen(BASEURL+filename, context=sslcontext)
            data: str = ret.read()
            dl_md5 = hashlib.md5(data).hexdigest()
            log.debug(f"MD5 verify test: downloaded '{dl_md5}' vs net '{net_md5}'.")
            if dl_md5 == net_md5:
                if NOMOD is False:
                    # ensure not read-only (only if exists)
                    if os.path.isfile(filename):
                        perms = stat.S_IMODE(os.lstat(filename).st_mode)
                        os.chmod(filename, perms | stat.S_IWRITE)

                    with open(filename, "wb") as f:
                        f.write(data)
                    log.info(f"'{filename}' updated.")
                else:
                    log.info(f"--nomod set: {filename} would've been updated.")
                actually_changed_a_file = True
                break
            else:
                count += 1
                log.debug(f"Validity check failed (file: {filename}, count: {count}).")
                if count > 3:
                    log.warning(f"Validity check failed for '{filename}' after 3 attempts.")
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
        ret = main()
    except:
        traceback.print_exc()
        input("fuck it broke. press enter to close")
    exit()
