from argparse import ArgumentParser
from pathlib import Path
from dataflow_designer_lib.pipeline_provider import SinaraPipelineProvider

arg_parser = ArgumentParser()

arg_parser.add_argument("--pipeline_dir", help="pipeline directory")
arg_parser.add_argument("--git_provider_type")
arg_parser.add_argument("--git_provider_api")
arg_parser.add_argument("--git_provider_url")
arg_parser.add_argument("--git_branch")
arg_parser.add_argument("--steps_folder_glob")
arg_parser.add_argument("--git_username")
arg_parser.add_argument("--git_password")

args = arg_parser.parse_args()

pipeline_provider = SinaraPipelineProvider()
pipeline_provider.checkout_pipeline(pipeline_dir = args.pipeline_dir,
                                git_provider_type = args.git_provider_type,
                                git_provider_url = args.git_provider_url,
                                git_provider_api = args.git_provider_api,
                                git_branch = args.git_branch,
                                steps_folder_glob = args.steps_folder_glob,
                                git_username = args.git_username,
                                git_password = args.git_password)
