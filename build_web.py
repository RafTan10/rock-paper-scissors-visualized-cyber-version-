"""
Build the web (browser) version of the game with pygbag.

    python build_web.py          -> builds into build/rps/build/web
    python build_web.py --serve  -> builds, then opens a test server at http://localhost:8000
    python build_web.py --itch   -> builds build/rps/build/web.zip, ready to upload to itch.io

Only the files the game needs are copied into build/rps first, so pygbag
doesn't pack the .venv folder or other extras.

web_template.tmpl is pygbag's default web page with the colours changed
to the game's black (instead of grey side bars and a light-blue loader).
"""
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
STAGE = os.path.join(HERE, "build", "rps")

FILES = ["main.py", "rps_visual.py", "try1.py", "opponents.py", "riddles.py", "story.py"]
FOLDERS = {"fonts": (".ttf", ".txt"), "sounds": (".ogg",)}

shutil.rmtree(STAGE, ignore_errors=True)
os.makedirs(STAGE)

for name in FILES:
    shutil.copy(os.path.join(HERE, name), STAGE)

for folder, exts in FOLDERS.items():
    os.makedirs(os.path.join(STAGE, folder))
    for name in os.listdir(os.path.join(HERE, folder)):
        if name.lower().endswith(exts):
            shutil.copy(os.path.join(HERE, folder, name), os.path.join(STAGE, folder))

cmd = [sys.executable, "-m", "pygbag", "--title", "Rock Paper Scissors", "--app_name", "rps",
       "--template", os.path.join(HERE, "web_template.tmpl")]
if "--itch" in sys.argv:
    cmd.append("--archive")          # build + zip it as build/rps/build/web.zip for itch.io
elif "--serve" not in sys.argv:
    cmd.append("--build")
cmd.append(STAGE)
sys.exit(subprocess.call(cmd))
