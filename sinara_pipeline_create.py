import json
import yaml
from pathlib import Path
from subprocess import STDOUT, run, call
import os
from getpass import getpass
import sys

from dataflow_designer_lib.github import create_github_repo
from dataflow_designer_lib.step_utils import create_step

from argparse import ArgumentParser

arg_parser = ArgumentParser()

arg_parser.add_argument("--step_template_git", help="step template git url")
arg_parser.add_argument("--step_template_nb_substep", help="the main notebook in step template")
arg_parser.add_argument("--current_dir", help="current directory")

args = arg_parser.parse_args()
#print(args)

SNR_STEP_TEMPLATE = args.step_template_git
SNR_STEP_TEMPLATE_SUBSTEP = args.step_template_nb_substep
CURRENT_DIR = args.current_dir

#TODO: make import of a proper function for creating repo, now only GitHub is chosen
    
#git_provider = input("Please, enter your Git provider among GitHub/Gitlab (default=GitHub): ") or 'GitHub'
#github_org_name = input(f"Please, enter your {git_provider} organization: ")
#github_token = getpass(f"Please, enter your token for managing {git_provider} repositories: ")

pipeline_name = input("Please, enter your Pipeline name: ")
pipeline_folder = input(f"Please, enter a folder to save '{pipeline_name}': ") or str(Path(CURRENT_DIR).resolve())

git_username = input("Please, enter your Git user name (default=jovyan): ") or "jovyan"
git_useremail = input("Please, enter your Git user email (default=jovyan@test.ru): ") or "jovyan@test.ru"
#save_git_creds = input(f"Would you like to store Git credentials once? WARNING: Currenly, only plain text is supported. y/n (default=y): ") or "y"

#if save_git_creds == "y":
#    run_result = run(f"git config --global credential.helper store && \
#                       (echo url=https://github.com; echo username={github_org_name}; echo password={github_token}; echo ) | git credential approve",
#                         shell=True, stderr=STDOUT, cwd=None)

#    if run_result.returncode !=0 :
#        raise Exception(f'Could not store Git credentials!')

with open('pipeline_manifest.yaml') as f:
    p_manifest_dict = yaml.safe_load(f)

for step in p_manifest_dict["steps"]:
    step_name = step["step_name"]
    step_repo_name = f"{pipeline_name}-{step_name}" 
    step_repo_path = pipeline_folder + "/" + step_repo_name + "/"
    
    run_result = run(f'cd {pipeline_folder} &&  \
                       rm -rf {step_repo_name} && \
                       git clone --recurse-submodules {SNR_STEP_TEMPLATE} {step_repo_name} && \
                       cd {step_repo_name} && \
                       git config user.email "{git_useremail}" && \
                       git config user.name "{git_username}"', 
                     shell=True, stderr=STDOUT, cwd=None)

    if run_result.returncode !=0 :
        raise Exception(f'Could not prepare a repository for SinaraML step with the name {step_repo_name}!')
         
    create_step(pipeline_name, step_repo_path, step["substeps"], SNR_STEP_TEMPLATE_SUBSTEP)

    run_result = run (f'git add -A && \
                        git commit -m "Adjust substep interface and step parameters" && \
                        git reset $(git commit-tree HEAD^{{tree}} -m "a new SinaraML step")',
                        shell=True, stderr=STDOUT, cwd=step_repo_path, executable="/bin/bash")
    if run_result.returncode !=0 :
        raise Exception(f'Could not prepare a repository for SinaraML step with the name {step_repo_name}!')
   