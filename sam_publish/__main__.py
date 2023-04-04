#!/usr/bin/env python3

from pathlib import Path
import argparse
import os
from os.path import dirname
import logging

import boto3
from .move_assets import move_assets, convert_to_yaml
from .inline_functions import inline_lambda_functions
from .sam_translate import transform_template
from .helpers import check_create_folder

LOG = logging.getLogger(__name__)

s3_client = boto3.client('s3')

parser = argparse.ArgumentParser(description=__doc__)

parser.add_argument(
    "--working_folder",
    help="Working folder for the input and output files.",
    type=Path
)
parser.add_argument(
    "--cfn-input-template",
    help="Name of JSON template to transform [default: template.json].",
    type=Path,
    default=Path("template.json"),
)
parser.add_argument(
    "--cfn-output-template",
    help="Name of JSON template to output [default: template.json].",
    type=Path,
    default=Path("template.json"),
)
parser.add_argument(
    "--target-asset-folder",
    help="Location the assets should be stored [default: ./Assets/].",
    type=Path,
    default=Path("./Assets/"),
)

parser.add_argument(
    "--lambda_folder",
    help="Location the lambda assets should be stored [default: Lambda].",
    type=Path,
    default=Path("Lambda"),
)

parser.add_argument(
    "--layer_folder",
    help="Location the layer assets should be stored [default: Layer].",
    type=Path,
    default=Path("Layer"),
)

parser.add_argument(
    "--statemachine_folder",
    help="Location the statemachine assets should be stored [default: Statemachine].",
    type=Path,
    default=Path("Statemachine"),
)

parser.add_argument(
    "--target-asset-bucket",
    help="Bucket the assets should be stored [default: ./Assets/].",
)

parser.add_argument(
    "--target-prefix",
    help="Prefix of the asset folders that items should be stored in [default: ''].",
    default='',
)

parser.add_argument(
    "--move-assets",
    help="Should references to the assets be moved to a different bucket",
    action="store_true",
    default=False,
)

parser.add_argument(
    "--debug",
    help="Enables debug logging",
    action="store_true",
)

parser.add_argument(
    "--verbose",
    help="Enables verbose logging",
    action="store_true",
)

cli_options, cli_cfn_parameters = parser.parse_known_args()

if cli_options.debug:
    logging.basicConfig(level=logging.DEBUG)
elif cli_options.verbose:
    logging.basicConfig(level=logging.INFO)
else:
    logging.basicConfig()

def main():
    input_template = CFN_INPUT_TEMPLATE
    output_template = f'{WORKING_FOLDER}/temp_template_1.json'
    transform_template(input_template, output_template)
    
    input_template = output_template
    output_template = f'{WORKING_FOLDER}/temp_template_2.yaml'
    if cli_options.move_assets:
        move_assets(input_template, output_template, TARGET_ASSET_BUCKET, TARGET_PREFIX, TARGET_ASSET_FOLDER, LAMBDA_FOLDER, LAYER_FOLDER, STATEMACHINE_FOLDER, s3_client)
    else:
        convert_to_yaml(input_template, output_template)

    input_template = output_template
    output_template = f'{WORKING_FOLDER}/temp_template_3.yaml'
    inline_lambda_functions(input_template, output_template, WORKING_FOLDER, s3_client)

    check_create_folder(dirname(CFN_OUTPUT_TEMPLATE))
    os.replace(output_template, CFN_OUTPUT_TEMPLATE)

if __name__ == "__main__":
    print("Running Script")
    WORKING_FOLDER = str(cli_options.working_folder)
    CFN_INPUT_TEMPLATE = str(cli_options.cfn_input_template)
    CFN_OUTPUT_TEMPLATE = str(cli_options.cfn_output_template)
    TARGET_ASSET_FOLDER = str(cli_options.target_asset_folder)
    LAMBDA_FOLDER = str(cli_options.lambda_folder)
    LAYER_FOLDER = str(cli_options.layer_folder)
    STATEMACHINE_FOLDER = str(cli_options.statemachine_folder)
    TARGET_ASSET_BUCKET = str(cli_options.target_asset_bucket)
    TARGET_PREFIX = str(cli_options.target_prefix)

    # cfn_parameters = {}
    # for cli_cfn_parameter in cli_cfn_parameters:
    #     print(cli_cfn_parameter)
    #     cfn_parameter_split = cli_cfn_parameter.split('=')
    #     cfn_parameters[cfn_parameter_split[0]] = cfn_parameter_split[1]

    main()