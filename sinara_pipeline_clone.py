from nbconvert import NotebookExporter
import json
import tempfile
import nbformat
import pprint
import pandas as pd
import yaml
from pathlib import Path
from subprocess import STDOUT, run, call
import os
from getpass import getpass
import shutil

from dataflow_designer_lib.github import create_github_repo
from dataflow_designer_lib.env import SNR_STEP_TEMPLATE, SNR_STEP_TEMPLATE_SUBSTEP

def get_sinara_user_work_dir():
    return os.getenv("JUPYTER_SERVER_ROOT") or '/home/jovyan/work'

def get_tmp_prepared():
    valid_tmp_target_path = f'/tmp/dataflow_fabric{os.getcwd().replace(get_sinara_user_work_dir(),"")}'
    os.makedirs(valid_tmp_target_path, exist_ok=True)
    tmp_path = Path('./tmp')
    if tmp_path.is_symlink():
        tmp_link = tmp_path.readlink()
        if tmp_link.as_posix() != valid_tmp_target_path:
            print("'tmp' dir is not valid, creating valid tmp dir...")
            tmp_path.unlink()                
            os.symlink(valid_tmp_target_path, './tmp', target_is_directory=True)
    else:
        if tmp_path.exists():
            print('\033[1m' + 'Current \'tmp\' folder inside your component is going to be deleted. It\'s safe, as \'tmp\' is moving to cache and will be recreated again.' + '\033[0m')
            shutil.rmtree(tmp_path)

        os.symlink(valid_tmp_target_path, './tmp', target_is_directory=True)


pp = pprint.PrettyPrinter(indent=4)

GIT_CRED_STORE_TIMEOUT=3600

#TODO: make import of a proper function for creating repo, now only GitHub is chosen
    
git_provider = input("Please, enter your Git provider among GitHub/Gitlab (default=GitHub): ") or 'GitHub'
github_org_name = input(f"Please, enter your {git_provider} organization: ")
github_token = getpass(f"Please, enter your token for managing {git_provider} repositories: ")

pipeline_name = input("Please, enter your Pipeline name: ")
pipeline_folder = input(f"Please, enter an existing folder to save '{pipeline_name}' (default=current_dir): ") or str(Path.cwd().resolve())

pipeline_folder = str(Path(pipeline_folder).resolve())

git_username = input("Please, enter your Git user name (default=jovyan): ") or "jovyan"
git_useremail = input("Please, enter your Git user email (default=jovyan@test.ru): ") or "jovyan@test.ru"
save_git_creds = input(f"Your pipeline steps will be cloned soon. Would you like to store Git credentials in memory for {GIT_CRED_STORE_TIMEOUT} seconds? WARNING: It may overwrite your stored github credentials. y/n (default=n): ") or "n"

if save_git_creds == "y":
    run_result = run(f"git config credential.helper 'cache --timeout='{GIT_CRED_STORE_TIMEOUT}'' && \
                       (echo url=https://github.com; echo username={github_org_name}; echo password={github_token}; echo ) | git credential approve", 
                         shell=True, stderr=STDOUT, cwd=None)

    if run_result.returncode !=0 :
        raise Exception(f'Could not store Git credentials in memory!')

with open('pipeline_manifest.yaml') as f:
    p_manifest_dict = yaml.safe_load(f)

tsrc_manifest = {"repos": []}
for step in p_manifest_dict["steps"]:
    step_name = step["step_name"]
    step_repo_name = f"{pipeline_name}-{step_name}" 
    step_repo_path = pipeline_folder + "/" + step_repo_name + "/"
    
    # TODO: consider choosing a needed Git provider
    step_repo_git = f"https://github.com/{github_org_name}/{step_repo_name}.git"
    
    tsrc_manifest_repo = {
        "dest": step_repo_name,
        "url": step_repo_git,
        "branch": "main"
    }
    
    tsrc_manifest["repos"].append(tsrc_manifest_repo)
    
with open('manifest.yml', 'w') as f:
    yaml.dump(tsrc_manifest, f, default_flow_style=False)

get_tmp_prepared()

tsrc_manifest_repo_path = str(Path(f"tmp/{pipeline_name}-manifest").resolve())

run_result = run(f'rm -rf {pipeline_folder}/.tsrc && \
                   rm -rf {tsrc_manifest_repo_path}.git && \
                   rm -rf {tsrc_manifest_repo_path} && \
                   git init --bare {tsrc_manifest_repo_path}.git && \
                   git clone {tsrc_manifest_repo_path}.git {tsrc_manifest_repo_path} && \
                   cp manifest.yml {tsrc_manifest_repo_path} && \
                   cd {tsrc_manifest_repo_path} && \
                   git add -A &&  \
                   git commit -m "Updated tsrc manifest" && \
                   git push && \
                   cd {pipeline_folder} && \
                   tsrc init {tsrc_manifest_repo_path}.git',
                 shell=True, stderr=STDOUT, cwd=None)
if run_result.returncode !=0 :
    raise Exception(f'Could not clone SinaraML pipeline!')
