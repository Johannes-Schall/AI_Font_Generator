"""This module provides functions to download font libraries from github repositories."""
import os
import subprocess
import json
import re
from concurrent.futures import ThreadPoolExecutor
import requests
from . import global_consts as g



GLYZPHAZZN_URL = 'https://storage.googleapis.com/magentadata/models/svg_vae/glyphazzn_urls.txt'


def get_font_dbs(db_flags):
    """ Prepare the download of font libraries from github repositories.

    Args:
        db_flags (Dictionary): Sets flags to download specific databases
        
    """

    path_target = g.PATH_RAW
    database_config = os.path.join(g.PATH_DB_CONFIGS, g.DBCONFIG)

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
        print("Loaded key for repository access.")

    # Check if target directory is already a git repository
    # if not, initialize it
    is_repo_initialized = os.path.isdir(os.path.join(path_db, '.git'))
    if not is_repo_initialized:
        print("Initializing Repo")
        subprocess.run(['git', 'init', path_db], check=True)
        subprocess.run(['git', 'config', 'core.sparseCheckout', 'true'],
                       cwd=path_db,
                       check=True)

    # Check if a remote repository exists
    # if not, add it
    existing_remotes = subprocess.check_output(
        ['git', 'remote'], cwd=path_db).decode().split()
    if 'origin' not in existing_remotes:
        print("Füge Remote hinzu")
        subprocess.run(['git', 'remote', 'add', '-f', 'origin', repo_url],
                       cwd=path_db,
                       check=True,
                       env=env)

    # Debugging:
    # existing_remotes = subprocess.check_output(
    #     ['git', 'remote'], cwd=path_db).decode().split()
    # if 'origin' not in existing_remotes:
    #     print("Adding Remote-Repository")
    #     subprocess.run(['git', 'remote', 'add', 'origin',
    #                    repo_url], cwd=path_db, check=True, env=env)

    #     print("Fetch Remote-Repository mit ausführlichen Informationen")
    #     fetch_output = subprocess.run(['git', 'fetch', '-v', 'origin', 'main'],
    #                                   cwd=path_db,
    #                                   capture_output=True,
    #                                   text=True,
    #                                   check=True,
    #                                   env=env)

    #     print("Standard Output:", fetch_output.stdout)
    #     print("Standard Error:", fetch_output.stderr)

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


def update_glyphazzn_list(path_glyphazzn, ):
    """ Download the latest link list for the glyphazzn dataset."""
    
    path_glyphazzn = g.PATH_RAW
    path_target = g.PATH_URL_LISTS
    
    # Check if target directory already exists
    if not os.path.isdir(path_glyphazzn):
        os.makedirs(path_glyphazzn)

    try:

        response = requests.get(GLYZPHAZZN_URL, timeout=15)
        response.raise_for_status()  # Raise exception if file not found

        filename = 'glyphazzn_raw.txt'
        save_path = os.path.join(path_glyphazzn, filename)

        with open(save_path, 'wb') as file:
            file.write(response.content)

        print("glyzphazzn link list updated.")
    except requests.RequestException as e:
        print(f"Download failed: {e}")
        print("Using existing list.")

    extract_urls(path_glyphazzn, filename, path_target)


def extract_urls(path_glyphazzn, filename, path_target):
    """Extracts URLs from a text file and saves them to a new file."""

    input_file_path = os.path.join(path_glyphazzn, filename)
    out_file_path = os.path.join(path_target, filename[:-8] + '.txt')

    if not os.path.exists(path_target):
        os.makedirs(path_target)

    # Regex zum Finden von URLs
    url_regex = r'https?://\S+'

    # Liste zum Speichern der gefundenen URLs
    extracted_urls = []

    # Datei öffnen und Zeile für Zeile lesen
    with open(input_file_path, 'r') as file:
        for line in file:
            # Suche nach URLs in jeder Zeile
            urls = re.findall(url_regex, line)
            extracted_urls.extend(urls)

    # Extrahierte URLs in einer neuen Datei speichern
    with open(out_file_path, 'w') as file:
        for url in extracted_urls:
            file.write(url + '\n')
    print(f"{filename} successfully extracted.")


def download_files_from_txts(path_source, path_target):
    """ Cycle through all txt files in a directory and queue the
        files for parallel download.

    """

    path_source = g.PATH_URL_LISTS
    path_target = g.PATH_RAW

    for _, _, files in os.walk(path_source):
        for file in files:
            if file.endswith('.txt'):
                print(f"Processing {file}...")
                destination_dir = os.path.join(path_target, file[:-4])

                urls = extract_list_from_txt(os.path.join(path_source, file))
                download_fonts_in_parallel(urls, destination_dir)


def extract_list_from_txt(path_sourcefile):
    """ Extract a list of URLs from a text file.

    Args:
        path_sourcefile (String): Path to the text file

    Returns:
        list[str]: URLs in a list
    """

    with open(path_sourcefile, 'r') as file:
        lines = file.readlines()
        urls = [line.strip() for line in lines]

    return urls


def download_fonts_in_parallel(urls, path_target):
    """ Set up a thread pool to download files in parallel.

    Args:
        urls (list): URLs to download
        path_target (String): Path to download directory
    """
    if not os.path.exists(path_target):
        os.makedirs(path_target)

    print(f"Checking {len(urls)} URLs...")
    with ThreadPoolExecutor(max_workers=10) as executor:
        for url in urls:
            executor.submit(download_from_list, url, path_target)
    # print(f"Downloaded {total_downloaded} files.")


def download_from_list(url_list, path_target):
    """ Download files from a list of URLs.

    Args:
        url (list): List of URLs
        path_target (String): Path to the target directory
    """

    files_downloaded = 0

    # if url_list is a list
    if isinstance(url_list, list):
        files_downloaded = 0
        for url in url_list:
            try:
                response = requests.get(url, timeout=1)
                if response.status_code == 200:
                    font_file_name = os.path.basename(url)
                    font_file_name_path = os.path.join(
                        path_target, font_file_name)
                    with open(font_file_name_path, 'wb') as f:
                        f.write(response.content)
                        files_downloaded += 1

                else:
                    pass  # print(f"URL not reachable: {url}")
            except FileNotFoundError:  # Exception as e:
                pass  # print(f"Error processing {url}: {e}")

        print(f"Downloaded {files_downloaded} of {len(url_list)} files.")
    # if url_list is a string (single url)
    elif isinstance(url_list, str):
        try:
            response = requests.get(url_list, stream=True, timeout=2)
            response.raise_for_status()
            filename = os.path.basename(url_list)
            filepath = os.path.join(path_target, filename)

            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
        except FileNotFoundError:
            pass
