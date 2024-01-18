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
        if 'interface' in cell["metadata"].get("tags", []):
            #pp.pprint(cell_source)
            #print(''.join(cell_source))
            df = pd.DataFrame({'source':[''.join(cell_source)]})
            df['Values'] = df['source'].str.replace(r'substep.interface\(([^()]+)\)', new_substep_interface)
            #print( df['Values'])
            print(''.join(df['Values']))
            cell_source_split = df['Values'].to_numpy()[0].split('\n')
            cell["source"] = [substr + '\n' for substr in cell_source_split[:-1]] + [cell_source_split[-1]]
    #pp.pprint(input_nb_dict)
    return input_nb_dict

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

tsrc_manifest = {"repos": []}
for step in p_manifest_dict["steps"]:
    step_name = step["step_name"]
    step_repo_name = f"{pipeline_name}-{step_name}" 
    step_repo_path = pipeline_folder + "/" + step_repo_name + "/"
    
    # TODO: consider choosing a needed Git provider
    step_repo_git = f"https://github.com/{github_org_name}/{step_repo_name}.git"
    
    tsrc_manifest_repo = {
        "dest": step_repo_name,
        "url": step_repo_git
    }
    
    tsrc_manifest["repos"].append(tsrc_manifest_repo)
    
    # create GitHub repo for a step
    response = create_github_repo(org_name=github_org_name, token=github_token, repo_name=step_repo_name, repo_description='This is your ' + step_name + ' step in pipeline ' + pipeline_name, is_private=True)
   
    print(response.raise_for_status())
    
    run_result = run(f'cd {pipeline_folder} &&  \
                       git clone --recurse-submodules {SNR_STEP_TEMPLATE} {step_repo_name} && \
                       cd {step_repo_name} && \
                       git config user.email "{git_useremail}" && \
                       git config user.name "{git_username}"', 
                     shell=True, stderr=STDOUT, cwd=None)

    if run_result.returncode !=0 :
        raise Exception(f'Could not prepare a repository for SinaraML step with the name {step_repo_name}!')
        
    substep_params = []
    for substep in step["substeps"]:
        substep_name = substep["substep_name"]
        substep_param = {
            "substep_name":f"{substep_name}.ipynb",
            "substep_params":
            {
                "param1":"None1",
                "param2":"None2"
            }
        }
        substep_params.append(substep_param)
            
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

        step_template_nb_name = step_repo_path + "/" + SNR_STEP_TEMPLATE_SUBSTEP
        output_nb_dict = change_substep_interface(step_template_nb_name, new_substep_interface)
        
        step_nb_name = step_repo_path + "/" + substep_name + ".ipynb"

        nbformat.write(nbformat.from_dict(output_nb_dict), step_nb_name, 4)
        
        Path(step_template_nb_name).unlink()
        
    with open(f"{step_repo_path}/params/step_params.json", 'r+', encoding='utf-8') as f:
        step_params = json.load(f)

        step_params["pipeline_params"]['pipeline_name'] = pipeline_name
        step_params["substeps_params"] = substep_params
        f.seek(0)

        json.dump(step_params, f, indent=4)
        f.truncate()
        

    run_result = run(f'cd {step_repo_path} && \
                       git remote set-url origin {step_repo_git} && \
                       git add -A &&  \
                       git commit -m "Set step parameters" && \
                       git reset $(git commit-tree HEAD^{{tree}} -m "a new SinaraML step") && \
                       git push', 
                     shell=True, stderr=STDOUT, cwd=None)

    if run_result.returncode !=0 :
        raise Exception(f'Could not create a repository for SinaraML step with the name {step_repo_name}!')

with open('manifest.yml', 'w') as f:
    yaml.dump(tsrc_manifest, f, default_flow_style=False)
