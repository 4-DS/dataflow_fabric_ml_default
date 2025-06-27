from argparse import ArgumentParser
from pathlib import Path
from dataflow_designer_lib.pipeline_provider import SinaraPipelineProvider, PipelineProviderException

arg_parser = ArgumentParser()
arg_parser.add_argument("--pipeline_dir")
arg_parser.add_argument("--pipeline_git_url")
arg_parser.add_argument("--git_username")
arg_parser.add_argument("--git_password")
arg_parser.add_argument("--git_provider")
arg_parser.add_argument("--git_provider_api")
arg_parser.add_argument("--git_provider_url")
arg_parser.add_argument("--git_auth_method")

args = arg_parser.parse_args()

try:
    pipeline_provider = SinaraPipelineProvider()
    pipeline_provider.push_pipeline(pipeline_dir = args.pipeline_dir,
                                    pipeline_git_url = args.pipeline_git_url,
                                    git_provider_type = args.git_provider,
                                    git_provider_url = args.git_provider_url,
                                    git_provider_api = args.git_provider_api,
                                    git_default_branch = 'main',
                                    git_username = args.git_username, git_password = args.git_password,
                                    git_auth_method = args.git_auth_method
                                   )
except PipelineProviderException as e:
    print(e)