import json
import yaml
from pathlib import Path
from subprocess import STDOUT, run, call
import os
from getpass import getpass
import shutil

import pprint

from dataflow_designer_lib.common import get_tmp_prepared 
from dataflow_designer_lib.github import get_pipeline_steps

pp = pprint.PrettyPrinter(indent=4)

#TODO: make import of a proper function for creating repo, now only GitHub is chosen
    
git_provider = input("Please, enter your Git provider among GitHub/Gitlab (default=GitHub): ") or 'GitHub'
github_org_name = input(f"Please, enter your {git_provider} organization: ")
github_token = getpass(f"Please, enter your token for managing {git_provider} repositories: ")

pipeline_name = input("Please, enter your Pipeline name: ")
pipeline_folder = input(f"Please, enter an existing folder to save '{pipeline_name}' (default=current_dir): ") or str(Path.cwd().resolve())

pipeline_folder = str(Path(pipeline_folder).resolve())

#git_username = input("Please, enter your Git user name (default=jovyan): ") or "jovyan"
#git_useremail = input("Please, enter your Git user email (default=jovyan@test.ru): ") or "jovyan@test.ru"

save_git_creds = input(f"Would you like to store Git credentials once? WARNING: Currenly, only plain text is supported. y/n (default=y): ") or "y"

if save_git_creds == "y":
    run_result = run(f"git config --global credential.helper store && \
                       (echo url=https://github.com; echo username={github_org_name}; echo password={github_token}; echo ) | git credential approve",
                         shell=True, stderr=STDOUT, cwd=None)

    if run_result.returncode !=0 :
        raise Exception(f'Could not store Git credentials!')

step_list = get_pipeline_steps(org_name=github_org_name, token=github_token, pipeline_name=pipeline_name)

tsrc_manifest = {"repos": []}
for step in step_list:
    step_repo_name = step["step_repo_name"]    
    step_repo_git = step["step_repo_git"]
    
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
    raise Exception(f'Could not clone SinaraML pipeline with the name {pipeline_name}!')
