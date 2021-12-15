#!/usr/bin/python3

import subprocess
from pathlib import Path

import mod_update

mod_update.main()
subprocess.Popen(Path.cwd().joinpath("legouniverse.exe"))
