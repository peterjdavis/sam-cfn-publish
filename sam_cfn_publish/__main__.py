#!/usr/bin/env python3

from pathlib import Path
import argparse
import os
from os.path import dirname
import logging
import boto3

from . import tags_metadata
from . import move_assets 
from . import inline_functions
from . import sam_translate
from . import helpers

def main():

    LOG = logging.getLogger(__name__)

    s3_client = boto3.client('s3')

    parser = argparse.ArgumentParser(description=__doc__)

    parser.add_argument(
        "--working-folder",
        help="Working folder for the input and output files.",
        type=Path,
        default=Path(helpers.get_temp_folder())
    )

    parser.add_argument(
        "--output-format",
        help="Format of the output template. [default: CFN]",
        choices=['SAM', 'CFN'],
        default='CFN'
    )
    parser.add_argument(
        "--cfn-input-template",
        help="Name of JSON template to transform [default: template.json].",
        type=Path,
        default=Path("template.json"),
    )
    parser.add_argument(
        "--cfn-output-template",
        help="Name of YAML template to output [default: template.yaml].",
        type=Path,
        default=Path("template.yaml"),
    )
    parser.add_argument(
        "--target-asset-folder",
        help="Location the assets should be stored [default: ./Assets/].",
        type=Path,
        default=Path("./Assets/"),
    )

    parser.add_argument(
        "--lambda-folder",
        help="Location the lambda assets should be stored.",
        default='',
    )

    parser.add_argument(
        "--layer-folder",
        help="Location the layer assets should be stored.",
        default='',
    )

    parser.add_argument(
        "--statemachine-folder",
        help="Location the statemachine assets should be stored",
        default='',
    )

    parser.add_argument(
        "--target-asset-bucket",
        help="Bucket the assets should be stored.",
    )

    parser.add_argument(
        "--target-prefix",
        help="Prefix of the asset folders that items should be stored in [default: ''].",
        default='',
    )

    parser.add_argument(
        "--move-assets",
        help="Should references to the assets be moved to a different bucket [default: False]",
        action="store_true",
        default=False,
    )

    parser.add_argument(
        "--tidy-tags-metadata",
        help="Should SAM tags and metadata be tidied up [Default: True]?",
        action="store_true",
        default=True,
    )

    parser.add_argument(
        "--add-layout-gaps",
        help="Should a new line be added between each resource for readability [Default: True]?",
        action="store_true",
        default=True,
    )

    parser.add_argument(
        "--debug",
        help="Enables debug logging [Default: False]",
        action="store_true",
        default=False,
    )

    parser.add_argument(
        "--verbose",
        help="Enables verbose logging [Default: True]",
        action="store_true",
        default=True
    )

    cli_options, cli_cfn_parameters = parser.parse_known_args()

    if cli_options.debug:
        logging.basicConfig(level=logging.DEBUG)
    elif cli_options.verbose:
        logging.basicConfig(level=logging.INFO)
    else:
        logging.basicConfig()

    WORKING_FOLDER = str(cli_options.working_folder)
    OUTPUT_FORMAT = str(cli_options.output_format)
    CFN_INPUT_TEMPLATE = str(cli_options.cfn_input_template)
    CFN_OUTPUT_TEMPLATE = str(cli_options.cfn_output_template)
    TARGET_ASSET_FOLDER = str(cli_options.target_asset_folder)
    LAMBDA_FOLDER = str(cli_options.lambda_folder)
    LAYER_FOLDER = str(cli_options.layer_folder)
    STATEMACHINE_FOLDER = str(cli_options.statemachine_folder)
    TARGET_ASSET_BUCKET = str(cli_options.target_asset_bucket)
    TARGET_PREFIX = str(cli_options.target_prefix)


    if OUTPUT_FORMAT == 'CFN':
        output_template_no = 1
        input_template = CFN_INPUT_TEMPLATE  
        output_template = f'{WORKING_FOLDER}/temp_template_{output_template_no}.json'
        sam_translate.transform_template(input_template, output_template)

    if cli_options.move_assets:
        if OUTPUT_FORMAT != 'CFN':
            output_template_no = 1
            input_template = CFN_INPUT_TEMPLATE  
            output_template = f'{WORKING_FOLDER}/temp_template_{output_template_no}.json'
        else:
            input_template = output_template
            output_template_no = output_template_no + 1
            output_template = f'{WORKING_FOLDER}/temp_template_{output_template_no}.json'
        move_assets.move_assets(OUTPUT_FORMAT, input_template, output_template, TARGET_ASSET_BUCKET, TARGET_PREFIX, TARGET_ASSET_FOLDER, LAMBDA_FOLDER, LAYER_FOLDER, STATEMACHINE_FOLDER, s3_client)

    if cli_options.tidy_tags_metadata:
        input_template = output_template
        output_template_no = output_template_no + 1
        output_template = f'{WORKING_FOLDER}/temp_template_{output_template_no}.json'
        tags_metadata.tidy_tags(input_template, output_template, WORKING_FOLDER)

    input_template = output_template
    output_template_no = output_template_no + 1
    output_template = f'{WORKING_FOLDER}/temp_template_{output_template_no}.yaml'
    helpers.convert_to_yaml(input_template, output_template)

    input_template = output_template
    output_template_no = output_template_no + 1
    output_template = f'{WORKING_FOLDER}/temp_template_{output_template_no}.yaml'
    inline_functions.inline_lambda_functions(OUTPUT_FORMAT, input_template, output_template, WORKING_FOLDER, s3_client)

    if cli_options.tidy_tags_metadata:
        input_template = output_template
        output_template_no = output_template_no + 1
        output_template = f'{WORKING_FOLDER}/temp_template_{output_template_no}.yaml'
        tags_metadata.tidy_metadata(input_template, output_template, cli_options.add_layout_gaps)

    output_folder = dirname(CFN_OUTPUT_TEMPLATE)
    if output_folder != '':
        helpers.check_create_folder(output_folder)
    os.replace(output_template, CFN_OUTPUT_TEMPLATE)

if __name__ == "__main__":
    main()