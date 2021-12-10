#!/usr/bin/python3
import os, shutil, hashlib, subprocess, stat, ssl, urllib.request

# i vomit every time i write this
TYPING = False
if TYPING:
    from typing import List

BASEURL = "https://runciman.hacksoc.org/~/ddm/mod/"
FILELIST = BASEURL+"modfilelist.txt"
VERBOSITY = 3

### helpers
def err(text : str):
    if VERBOSITY >= 1:
        print(f"[ERR] {text}")
def warn(text : str):
    if VERBOSITY >= 2:
        print(f"[WRN] {text}")
def info(text : str):
    if VERBOSITY >= 3:
        print(f"[INF] {text}")
def verbose(text : str):
    if VERBOSITY >= 4:
        print(f"[INF] {text}")
def debug(text : str):
    if VERBOSITY >= 5:
        print(f"[DBG] {text}")

### funny globals go brrr
sslcontext = ssl.create_default_context()
sslcontext.check_hostname = False
sslcontext.verify_mode = ssl.VerifyMode.CERT_NONE

### main
def main() -> int:
    local_lines = [] #NOTE: needs to have newlines stripped!
    if os.path.isfile("modfilelist.txt"):
        with open("modfilelist.txt", "r") as f:
            local_lines = f.readlines()
    else:
        debug("No local modfilelist, setting revision to 0")
        local_lines = ["0",""]

    ret = urllib.request.urlopen(FILELIST, context=sslcontext)
    net_lines = ret.read().decode("utf-8").split("\n") # type: List[str]
    #NOTE: doesn't need newlines stripped

    local_rev = int(local_lines[0].strip("\n"))
    net_rev = int(net_lines[0])
    if net_rev > local_rev:
        print(f"Found mod update (revision {local_rev} -> {net_rev}).")
        with open("modfilelist.txt", "w") as f:
            f.writelines(net_lines)
        _ = update(net_lines[1:])
        return 0

    print(f"Mod is up to date (revision {local_rev}).")
    return 0

def update(filelines : str) -> int:
    not_ok = 0
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
            info(f"Made a backup of {filename}")
        else:
            # get local md5
            local_md5 = "file doesn't exist"
            if os.path.isfile(filename):
                data = open(filename, "rb").read()
                local_md5 = hashlib.md5(data).hexdigest()

            debug(f"MD5 download test: local '{local_md5}' vs net '{net_md5}'")
            # if md5s match, don't download this file
            if local_md5 == net_md5:
                verbose(f"'{filename}' skipped, unchanged from current.")
                continue

        # file should be downloaded if we get here
        count = 0
        while True:
            ret = urllib.request.urlopen(BASEURL+filename, context=sslcontext)
            data = ret.read() # type: str
            dl_md5 = hashlib.md5(data).hexdigest()
            debug(f"MD5 verify test: downloaded '{dl_md5}' vs net '{net_md5}'")
            if dl_md5 == net_md5:
                # ensure not read-only
                os.chmod(filename, stat.S_IWRITE)
                with open(filename, "wb") as f:
                    f.write(data)
                info(f"'{filename}' updated.")
                break
            else:
                count += 1
                debug(f"Download check failed (file: {filename}, count: {count})")
                if count > 3:
                    warn(f"Download check failed for '{filename}' after 3 attempts.")
                    not_ok = 1
                    break
    
    return not_ok

if __name__ == "__main__":
    exit(main())