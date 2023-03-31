#!/usr/bin/env python3

from pathlib import Path
from . import update_references
import boto3
import argparse


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
    "--target-asset-bucket",
    help="Bucket the assets should be stored [default: ./Assets/].",
)

cli_options, cli_cfn_parameters = parser.parse_known_args()

if __name__ == "__main__":

    print("Running Script")
    WORKING_FOLDER = str(cli_options.working_folder)
    CFN_INPUT_TEMPLATE = str(cli_options.cfn_input_template)
    CFN_OUTPUT_TEMPLATE = WORKING_FOLDER + '/' + \
        str(cli_options.cfn_output_template)
    TARGET_ASSET_FOLDER = str(cli_options.target_asset_folder)
    TARGET_ASSET_BUCKET = str(cli_options.target_asset_bucket)

    cfn_parameters = {}
    for cli_cfn_parameter in cli_cfn_parameters:
        print(cli_cfn_parameter)
        cfn_parameter_split = cli_cfn_parameter.split('=')
        cfn_parameters[cfn_parameter_split[0]] = cfn_parameter_split[1]

    process_template()