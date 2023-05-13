import json
import logging
from functools import reduce

import boto3

from samtranslator.model.exceptions import InvalidDocumentException
from samtranslator.public.translator import ManagedPolicyLoader
from samtranslator.translator.transform import transform
from samtranslator.yaml_helper import yaml_parse

LOG = logging.getLogger(__name__)
iam_client = boto3.client("iam")

def transform_template(input_file_path, output_file_path):  # type: ignore[no-untyped-def]
    with open(input_file_path) as f:
        sam_template = yaml_parse(f)  # type: ignore[no-untyped-call]

    try:
        cloud_formation_template = transform(sam_template, {}, ManagedPolicyLoader(iam_client))
        cloud_formation_template_prettified = json.dumps(cloud_formation_template, indent=1)

        with open(output_file_path, "w") as f:
            f.write(cloud_formation_template_prettified)

        LOG.debug("Wrote transformed CloudFormation template to: %s", output_file_path)
    except InvalidDocumentException as e:
        error_message = reduce(lambda message, error: message + " " + error.message, e.causes, e.message)
        LOG.error(error_message)
        errors = (cause.message for cause in e.causes)
        LOG.error(errors)