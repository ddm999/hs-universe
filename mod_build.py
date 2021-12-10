#!/usr/bin/python3
import os, shutil, hashlib, subprocess

def main() -> int:
    # remove old folder
    if os.path.exists("mod"):
        while True:
            try:
                shutil.rmtree("mod")
                break
            except:
                continue

    md5s = {}
    with open("mod_files.txt", "r") as f:
        lines = f.readlines()

        for line in lines:
            # stupid newlines
            line = line.strip("\r\n")

            # ignore empty lines and comment lines
            if line == "" or line.startswith("#"):
                continue

            # copy to mod folder
            os.makedirs(os.path.dirname(f"mod/{line}"), exist_ok=True)
            shutil.copyfile(line, f"mod/{line}")

            # add md5 to dict
            data = open(f"mod/{line}", "rb").read()
            md5 = hashlib.md5(data).hexdigest()
            md5s[line] = md5

    # find revision number
    revision = 1
    if os.path.isfile("mod_revcount.txt"):
        with open("mod_revcount.txt", "r") as f:
            revision = int(f.readline()) + 1
    
    # save revision number
    with open("mod_revcount.txt", "w") as f:
        f.write(f"{revision}\n")

    # write filelist
    with open("mod/modfilelist.txt", "w") as f:
        f.write(f"{revision}\n")
        for filename, md5 in md5s.items():
            f.write(f"{filename} {md5}\n")

    print(f"Updated mod to revision {revision}.")
    print(f"Press CTRL+C to skip upload.")
    subprocess.run("scp -r mod ddm@runciman.hacksoc.org:~/private_html")

    return 0

if __name__ == "__main__":
    exit(main())