#!/usr/bin/python
from git import Repo
import logging
import os
import yaml

logger = logging.getLogger(__name__)

SYS_SETTINGS_FN = "system_settings.yaml"
REPO_LIST_FN = "repo_listing.yaml"


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    with open(SYS_SETTINGS_FN) as stream:
        try:
            sys_settings = yaml.safe_load(stream)
        except yaml.YAMLError:
            sys_settings = {}
            logger.error(exc_info=True)
    with open(REPO_LIST_FN) as stream:
        try:
            repo_list = yaml.safe_load(stream)
        except yaml.YAMLError:
            repo_list = []
            logger.error(exc_info=True)

    def clone_progress(op_code, cur_count, max_count=None, message=''):
        logger.info(f"Progress: {op_code}, {cur_count}/{max_count}: {message}")

    storage_root = sys_settings["storage_root"]
    for repo in repo_list:
        url = repo["url"]
        protocol,path=url.split("://")
        path_elements = path.split("/")
        path_elements_sanitized = [el for el in path_elements if el != ".."]
        local_repo_path = os.path.join(storage_root, *path_elements_sanitized)
        if os.path.isdir(local_repo_path):
            logger.info(f"Will fetch {repo} into {local_repo_path}")
            repo = Repo(local_repo_path)
            logger.info(f"Repo {'is' if repo.bare else 'is not'} bare.")
            repo.remote("origin").fetch(refspec='+refs/heads/*:refs/heads/*', progress=clone_progress)
        else:
            logger.info(f"Will clone {repo} into {local_repo_path}")
            os.makedirs(local_repo_path, exist_ok=True)
            repo = Repo.clone_from(url, local_repo_path, clone_progress, multi_options=["--bare"])
    