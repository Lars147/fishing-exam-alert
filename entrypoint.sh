#!/bin/sh

## Do whatever you need with env vars here ...
python3 -u ./fishing_exam_alert/check.py

# Hand off to the CMD
exec "$@"