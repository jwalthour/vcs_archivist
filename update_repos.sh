#!/bin/bash

# Run update_repos.py.  Intended to be run as a cronjob owned by the user `librarian`.

cd /home/librarian/vcs_archivist
source ./venv/bin/activate
python update_repos.py