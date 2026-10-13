# Security

## What the skill does on your machine

- It reads files on the drive you name. It never writes to that drive.
- It writes only inside the run folder you start the agent in: `clean-copy/`, `report/`, and `_private/`.
- It does not need network access during a run. At the start it checks that a web request and a write to your home folder both fail. If either succeeds, it stops.
- It runs local tools: Python, tesseract, poppler, qpdf, exiftool, 7-Zip, and readpst.
- Your coding agent sends what it reads to your AI provider. The skill therefore keeps file names and document content out of the agent's view by default; local scripts do the reading.

## Verifying a release

Every release has a `SHA256SUMS` file. Releases are never changed after publication; a fix gets a new version number. Check the archive before extracting it, as shown in the README.

## Reporting a problem

Contact The General Data Company through [thegeneraldata.com](https://thegeneraldata.com). Please do not include file contents or personal data in a report.
