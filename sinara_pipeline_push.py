import json
import yaml
from pathlib import Path
from subprocess import STDOUT, run, call
import os
from getpass import getpass

from dataflow_designer_lib.github import create_github_repo
from dataflow_designer_lib.step_utils import get_step_folders

GIT_CRED_STORE_TIMEOUT=3600

#TODO: make import of a proper function for creating repo, now only GitHub is chosen
    
git_provider = input("Please, enter your Git provider among GitHub/Gitlab (default=GitHub): ") or 'GitHub'
github_org_name = input(f"Please, enter your {git_provider} organization: ")
github_token = getpass(f"Please, enter your token for managing {git_provider} repositories: ")

pipeline_name = input("Please, enter your Pipeline name: ")
        
steps_folder_glob = input(f"Please, enter a glob to load '{pipeline_name}' like /some_path/steps_folder/*. (default=./*): ") or "./*"

save_git_creds = input(f"Would you like to store Git credentials once? WARNING: Currenly, only plain text is supported. y/n (default=y): ") or "y"

if save_git_creds == "y":
    run_result = run(f"git config --global credential.helper store && \
                       (echo url=https://github.com; echo username={github_org_name}; echo password={github_token}; echo ) | git credential approve",
                         shell=True, stderr=STDOUT, cwd=None)

    if run_result.returncode !=0 :
        raise Exception(f'Could not store Git credentials!')

step_folders = get_step_folders(steps_folder_glob)

for step_folder in step_folders:
    step_folder_split = Path(step_folder).name.split("-")
    step_name = '-'.join(step_folder_split[1::]) if len(step_folder_split) > 1 else None
    if step_name:
        step_repo_name = f"{pipeline_name}-{step_name}" 
        step_repo_path = step_folder
        
        # TODO: consider choosing a needed Git provider
        step_repo_git = f"https://github.com/{github_org_name}/{step_repo_name}.git"
        
        # create GitHub repo for a step
        response = create_github_repo(org_name=github_org_name, token=github_token, repo_name=step_repo_name, repo_description='This is your ' + step_name + ' step in pipeline ' + pipeline_name, is_private=True)
       
        #print(response.raise_for_status())       
        run_result = run (f'git remote set-url origin {step_repo_git} && \
                            git push',
                           shell=True, stderr=STDOUT, cwd=step_repo_path, executable="/bin/bash")
        if run_result.returncode !=0 :
            raise Exception(f'Could not create a repository for SinaraML step with the name {step_repo_name}!')
         #break
