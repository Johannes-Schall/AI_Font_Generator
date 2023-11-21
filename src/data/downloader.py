"""This module provides functions to download font libraries from github repositories."""
import os
import subprocess
import json

DBCONFIG = "source.json"


def get_fonts(db_flags, path_config, path_target):
    """ Prepare the download of font libraries from github repositories.

    Args:
        db_flags (Dictionary): Sets flags to download specific databases
        path_config (String): Path to the directory holding all configuration files
        path_target (String): Path to which the font libraries should be downloaded
    """

    database_config = os.path.join(path_config, DBCONFIG)

    # read database config file from json
    with open(database_config, 'r') as infile:
        databases = json.load(infile)

    for key, value in db_flags.items():
        if (key in databases) and (value):
            get_github_db(path_target,
                          key,
                          databases[key]['url'],
                          databases[key]['directories'],
                          databases[key]['private'])


def get_github_db(path_target, db_name, repo_url, directory_list=None, private=False):
    """ Get font libraries from github repositories by cloning
        or fetching data. To make sure that locally deleted files
        are pulled from the remote repository, the local repository
        is resetted to the remote repository.

    Args:
        path_target (String): Path to the target directory
        db_name (String): Name of the database
        repo_url (String): URL of the remote repository
        directory_list (list, optional): Selected directories. Defaults to None
        private (bool, optional): Flag if the repository is private. Defaults to False
    """

    print(f"Accessing {db_name}.")

    path_db = os.path.join(path_target, db_name)

    # Check if target directory already exists
    if not os.path.isdir(path_db):
        os.makedirs(path_db)

    # Prepare SSH key for private repositories
    env = None
    if private:
        env = os.environ.copy()
        ssh_key_path = os.path.join(path_target, db_name + "_key")
        env["GIT_SSH_COMMAND"] = f"ssh -i {ssh_key_path}"

    # Check if target directory is already a git repository
    # if not, initialize it
    is_repo_initialized = os.path.isdir(os.path.join(path_db, '.git'))
    if not is_repo_initialized:
        subprocess.run(['git', 'init', path_db], check=True)
        subprocess.run(['git', 'config', 'core.sparseCheckout', 'true'],
                       cwd=path_db,
                       check=True)

    # Check if a remote repository exists
    # if not, add it
    existing_remotes = subprocess.check_output(
        ['git', 'remote'], cwd=path_db).decode().split()
    if 'origin' not in existing_remotes:
        subprocess.run(['git', 'remote', 'add', '-f', 'origin',
                       repo_url], cwd=path_db, check=True)

    # If only specific directories should be cloned or updated,
    # write the sparse checkout configuration file
    if len(directory_list) != 0:
        with open(os.path.join(path_db, '.git', 'info', 'sparse-checkout'), 'w') as file:
            for directory in directory_list:
                file.write(directory + '\n')
        print(f"{len(directory_list)} directories for transfer.")

    # Execution:
    # Always do fetch and checkout
    # Do hard reset of local repo only if repo was already initialized
    try:
        print("Transferring files...")
        subprocess.run(['git', 'fetch', 'origin', 'main'],
                       cwd=path_db,
                       check=True,
                       env=env)

        if is_repo_initialized:
            subprocess.run(['git', 'reset', '--hard', 'origin/main'],
                           cwd=path_db,
                           check=True)

        subprocess.run(['git', 'checkout', 'origin/main'],
                       cwd=path_db, check=True)
        print("File transfer successful")
    except subprocess.CalledProcessError as e:
        print(f"Error: {e}")
