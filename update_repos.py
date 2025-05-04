#!/usr/bin/python
import logging.handlers
from git import Repo
import logging
import os
import shutil
import yaml

logger = logging.getLogger(__name__)

SYS_SETTINGS_FN = "system_settings.yaml"
REPO_LIST_FN = "repo_listing.yaml"
LOG_FORMAT = "%(asctime)s %(levelname)s %(message)s"
LOG_TIME_FORMAT = "%Y-%m-%d %H:%M:%S"
LOG_FILENAME = "repo_update.log"
SINGLE_LOG_MAX_SIZE_B = 10 * 1024 * 1024
TOTAL_LOG_COUNT = 10

if __name__ == "__main__":
    with open(SYS_SETTINGS_FN) as stream:
        # Can't set up logging without reading log file location from here.
        # So don't catch any exceptions, just explode.
        sys_settings = yaml.safe_load(stream)
    os.makedirs(sys_settings["log_dir"], exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format=LOG_FORMAT,
        datefmt=LOG_TIME_FORMAT,
        handlers=[
            logging.handlers.RotatingFileHandler(
                os.path.join(sys_settings["log_dir"], LOG_FILENAME),
                maxBytes=SINGLE_LOG_MAX_SIZE_B,
                backupCount=TOTAL_LOG_COUNT,
            ),
            logging.StreamHandler(),
        ],
    )
    with open(REPO_LIST_FN) as stream:
        try:
            repo_list = yaml.safe_load(stream)
        except yaml.YAMLError:
            repo_list = []
            logger.error(exc_info=True)

    def default_progress(op_code, cur_count, max_count=None, message=""):
        logger.info(f"Progress: {op_code}, {cur_count}/{max_count}: {message}")

    storage_root = sys_settings["storage_root"]
    storage_min_free_space_gb = sys_settings["storage_min_free_space_gb"]

    # Do we have enough space?
    total_b, used_b, free_b = shutil.disk_usage(storage_root)
    storage_desc = f"Have {free_b / (1024**3):.3f} GB free out of required {storage_min_free_space_gb:.3f} GB"
    if free_b >= (1024**3) * storage_min_free_space_gb:
        logger.info(f"{storage_desc}; will update.")
    else:
        logger.error(f"{storage_desc}; will not update.")
        exit(2)

    for category_name, repos in repo_list.items():
        logger.info(f"Updating category: {category_name}")
        for repo in repos:
            url = repo["url"]
            protocol, path = url.split("://")
            path_elements = path.split("/")
            path_elements_sanitized = [el for el in path_elements if el != ".."]
            local_repo_path = os.path.join(storage_root, *path_elements_sanitized)
            if os.path.isdir(local_repo_path):
                logger.info(f"Will fetch {repo} into {local_repo_path}")
                repo = Repo(local_repo_path)
                logger.info(f"Repo {'is' if repo.bare else 'is not'} bare.")
                repo.remote("origin").fetch(refspec="+refs/heads/*:refs/heads/*")
            else:
                logger.info(f"Will clone {repo} into {local_repo_path}")
                os.makedirs(local_repo_path, exist_ok=True)
                repo = Repo.clone_from(url, local_repo_path, multi_options=["--bare"])
    logger.info("Done.")
