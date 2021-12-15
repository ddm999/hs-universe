#!/usr/bin/python3

import os
import subprocess
import sys
from pathlib import Path

import mod_update

# set the cwd to the script dir - on windows with windows store python cwd is system32 for some reason
os.chdir(Path(sys.argv[0]).resolve().parent)

mod_update.main(True)
subprocess.Popen(Path.cwd().joinpath("legouniverse.exe"))
