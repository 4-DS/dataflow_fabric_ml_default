from dataflow_designer_lib.pipeline_provider import SinaraPipelineProvider


from argparse import ArgumentParser
from pathlib import Path
from dataflow_designer_lib.pipeline_provider import SinaraPipelineProvider

arg_parser = ArgumentParser()

arg_parser.add_argument("--pipeline_dir", help="pipeline directory")
arg_parser.add_argument("--git_provider_type")
arg_parser.add_argument("--steps_folder_glob")
arg_parser.add_argument("--new_name")

args = arg_parser.parse_args()

pipeline_provider = SinaraPipelineProvider()
pipeline_provider.update_name_for_pipeline(pipeline_dir = args.pipeline_dir,
                                git_provider_type = args.git_provider_type,
                                steps_folder_glob = args.steps_folder_glob,
                                new_name = args.new_name)
