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

from dataflow_designer_lib.github import create_github_repo
from dataflow_designer_lib.env import SNR_STEP_TEMPLATE, SNR_STEP_TEMPLATE_SUBSTEP

pp = pprint.PrettyPrinter(indent=4)

def change_substep_interface(step_template_nb_name, new_substep_interface):
    
    nb_body, inputs = NotebookExporter().from_filename(step_template_nb_name)
    input_nb_dict = json.loads(nb_body)
    output_nb_dict = input_nb_dict.copy()

    #pp.pprint(input_nb_dict["cells"])
    # locate substep interface 
    for cell in input_nb_dict["cells"]:
        cell_source = cell["source"]
        for cell_source_line in cell_source:
            if "substep.interface" in cell_source_line:
                #pp.pprint(cell_source)
                #print(''.join(cell_source))
                df = pd.DataFrame({'source':[''.join(cell_source)]})
                df['Values'] = df['source'].str.replace(r'substep.interface\(([^()]+)\)', new_substep_interface)
                #print( df['Values'])
                print(''.join(df['Values']))
                cell_source_split = df['Values'].to_numpy()[0].split('\n')
                cell["source"] = [substr + '\n' for substr in cell_source_split[:-1]] + [cell_source_split[-1]]
    pp.pprint(input_nb_dict)
    return input_nb_dict

# TODO
# amend do_step.ipynb right in step repo

# Define pipeline name based on DataFlow Designer repo name

GIT_CRED_STORE_TIMEOUT=3600

#TODO: make import of a proper function for creating repo, now only GitHub is chosen
    
git_provider = input("Please, enter your Git provider among GitHub/Gitlab (default=GitHub): ") or 'GitHub'
github_org_name = input(f"Please, enter your {git_provider} organization: ")
github_token = getpass(f"Please, enter your token for managing {git_provider} repositories: ")

pipeline_name = input("Please, enter your Pipeline name: ")
pipeline_folder = input(f"Please, enter a folder to save '{pipeline_name}': ") or str(Path.cwd().resolve())

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
    
#pp.pprint(p_manifest_dict)

for step in p_manifest_dict["steps"]:
    step_name = step["step_name"]
    step_repo = f"{pipeline_name}-{step_name}"
    
    # create GitHub repo for a step
    response = create_github_repo(org_name=github_org_name, token=github_token, repo_name=step_repo, repo_description='This is your ' + step_name + ' step in pipeline ' + pipeline_name, is_private=True)
   
    print(response)
    
    # TODO: consider choosing a needed Git provider
    run_result = run(f'cd {pipeline_folder} &&  \
                    git clone --recurse-submodules {SNR_STEP_TEMPLATE} {step_repo} && \
                    cd {step_repo} && \
                    git config user.email "{git_useremail}" && \
                    git config user.name "{git_username}" && \
                    git remote set-url origin https://github.com/{github_org_name}/{step_repo}.git', 
                     shell=True, stderr=STDOUT, cwd=None)

    if run_result.returncode !=0 :
        raise Exception(f'Could not create GitHub repo!')
    
    for substep in step["substeps"]:
        substep_name = substep["substep_name"]
        step_inputs = []
        step_outputs = []
        for step_input in substep["inputs"]:
            step_inputs.append('{ STEP_NAME: "' + step_input.get("step_name") + '", ENTITY_NAME: "' + step_input.get("entity_name") + '" },')

        for step_output in substep["outputs"]:
            step_outputs.append('{ ENTITY_NAME: "' + step_output.get("entity_name") + '" },')

        new_substep_interface = """
    substep.interface(

        inputs =
        [
    {step_inputs}
        ],
        outputs = 
        [
    {step_outputs}
        ]
    )""".format(step_inputs=''.join(['            ' + step_input + '\n' for step_input in step_inputs]), step_outputs=''.join(['            ' + step_output + '\n' for step_output in step_outputs]))
        #print(new_substep_interface)

        step_template_nb_name = pipeline_folder + "/" + step_repo + "/" + SNR_STEP_TEMPLATE_SUBSTEP
        output_nb_dict = change_substep_interface(step_template_nb_name, new_substep_interface)
        
        step_nb_name = pipeline_folder + "/" + step_repo + "/" + substep_name + ".ipynb"

        nbformat.write(nbformat.from_dict(output_nb_dict), step_nb_name, 4)
        
        Path(step_template_nb_name).unlink()
    

    run_result = run(f'cd {step_repo} && \
                    sed -i "s/\"pipeline\"/\"{pipeline_name}\"/g" ./params/step_params.json && \
                    git add -A &&  \
                    git commit -m "Set step and pipeline parameters" && \
                    git reset $(git commit-tree HEAD^{{tree}} -m "a new SinaraML step") && \
                    git push', 
                     shell=True, stderr=STDOUT, cwd=None)

    if run_result.returncode !=0 :
        raise Exception(f'Could not create SinaraML step repo!')
