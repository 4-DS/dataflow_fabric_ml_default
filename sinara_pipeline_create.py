from argparse import ArgumentParser
from pathlib import Path
from dataflow_designer_lib.pipeline_provider import SinaraPipelineProvider


arg_parser = ArgumentParser()
arg_parser.add_argument("--pipeline_type")
arg_parser.add_argument("--pipeline_name")
arg_parser.add_argument("--pipeline_dir")
arg_parser.add_argument("--git_step_template_url")
arg_parser.add_argument("--step_template_nb_substep")
arg_parser.add_argument("--git_step_template_username")
arg_parser.add_argument("--git_step_template_password")
arg_parser.add_argument("--git_provider")
arg_parser.add_argument("--git_provider_api")
arg_parser.add_argument("--git_provider_url")
arg_parser.add_argument("--git_username")
arg_parser.add_argument("--git_useremail")

# #arg_parser.add_argument("--git_provider_step_template_url", help="git provider base url where step template resides")    
# arg_parser.add_argument("--git_provider_organization_api", help="git provider api url in organization")    
# arg_parser.add_argument("--git_provider_organization_url", help="git provider base url in organization")

# arg_parser.add_argument("--git_step_template_url", help="step template url")
# arg_parser.add_argument("--step_template_nb_substep", help="the main notebook in step template")
# arg_parser.add_argument("--current_dir", help="current directory")      
# arg_parser.add_argument("--git_step_template_username", help="login to clone step template")
# arg_parser.add_argument("--git_step_template_password", help="password to clone step template")

args = arg_parser.parse_args()

# SNR_STEP_TEMPLATE = args.git_step_template_url
# SNR_STEP_TEMPLATE_SUBSTEP = args.step_template_nb_substep
# CURRENT_DIR = args.current_dir

# git_public_user_sent = args.git_step_template_username is not None and args.git_step_template_password
# if git_public_user_sent:
#     GIT_STEP_TEMPLATE_USERNAME = args.git_step_template_username
#     GIT_STEP_TEMPLATE_PASSWORD = args.git_step_template_password

# git_provider = self.git_provider #input("Please, enter your Git provider among GitHub/GitLab (default=GitLab): ") or 'GitLab'
# product_name = None
# if git_provider == 'GitLab':
#     product_name = input("Please, enter your Product name: ") or 'fabric_test_product'
# elif git_provider == 'GitHub':
#     pass

# pipeline_name = input("Please, enter your Pipeline name: ") or 'fabric_test_pipeline'
# pipeline_folder = input(f"Please, enter a folder to save '{pipeline_name}': ") or str(Path(CURRENT_DIR).resolve())

# git_default_branch = input("Please, enter your Git default branch: ")
# git_username = input("Please, enter your Git user name (default=data_scientist_name): ") or "data_scientist_name"
# git_useremail = input("Please, enter your Git user email (default=data_scientist_name@example.com): ") or "data_scientist_name@example.com"

pipeline_provider = SinaraPipelineProvider()

pipeline_manifest_path = str(Path(__file__).parent.resolve()) + '/' + f"pipeline_manifest_{args.pipeline_type}.yaml"
print(f'Trying pipeline manifest in {pipeline_manifest_path}')

pipeline_provider.create_pipeline(pipeline_manifest_path = pipeline_manifest_path,
                                  pipeline_dir = args.pipeline_dir,
                                  pipeline_name = args.pipeline_name,
                                  git_provider = args.git_provider,
                                  git_step_template_url = args.git_step_template_url,
                                  step_template_nb_substep = args.step_template_nb_substep,
                                  git_step_template_username = args.git_step_template_username,
                                  git_step_template_password = args.git_step_template_password,
                                  git_username = args.git_username,
                                  git_useremail = args.git_useremail
                                 )
