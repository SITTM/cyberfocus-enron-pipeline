# Setup — what to do

## Before you start

- You do **not** need Python. Do not install it.
- You need ~6 GB free disk and an internet connection.
- Ignore anything you have been told about needing Python 3.8. It is wrong.

## Do this

- Download/clone the repo.
- Double-click **`SETUP-WINDOWS.cmd`**.
- Leave it alone. It takes **2–4 hours**, most of it unpacking the email archive.
- It is finished when it prints `SETUP COMPLETE. Your environment is verified.`

## While it runs

- It prints a progress line every 60 seconds. If you can see those, it is working.
- Do not close the window.
- If your machine sleeps or reboots, just double-click the file again — it carries
  on from where it stopped, it does not start over.

## If it fails

- It writes **`bootstrap-report.json`** in the repo folder.
- Send that one file to Jez. Nothing else — no screenshots.
- Then stop. Do not try to fix it yourself, and do not install Python to "help".

## After it succeeds

- Tell Jez. Do not start annotating yet.
- To build the annotation sheets when asked:
  - Open PowerShell in the repo folder.
  - Run: `.venv\Scripts\python.exe scripts\prepare_annotation.py --reviewers <your-name>`
  - Takes ~1 hour. Safe to re-run; it resumes.

## Rules

- Never edit the expected numbers in a test to make it pass.
- If something looks wrong, ask. Do not work around it quietly — a silent
  workaround on one machine makes everyone's results incomparable.

## Optional, makes it much faster

- Before starting, in an **Administrator** PowerShell:
  `Add-MpPreference -ExclusionPath 'C:\enron'`
- Skip this if your IT policy says not to. Error `0x800106ba` just means you have
  no Defender running — ignore it and carry on.
