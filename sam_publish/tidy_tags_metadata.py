import logging
import cfn_flip
from .helpers import write_json_file

LOG = logging.getLogger(__name__)

def tidy_tags(cfn_input_template, cfn_output_template, working_folder):
    with open(cfn_input_template) as f:
        str_cfn = f.read()

    cfn = cfn_flip.load_json(str_cfn)
    resources = cfn["Resources"]

    for key, value in resources.items():
        LOG.info('Tidying tags in %s', key)
        if "Tags" in value["Properties"]:
            tags = value["Properties"]["Tags"]
            i = 0
            for tag in tags:
                if tag['Key'] == 'lambda:createdBy' and tag['Value'] == 'SAM':
                    LOG.info('About to delete tag')
                    del value["Properties"]["Tags"][i]
                    i = i + 1
            if value["Properties"]["Tags"] == []:
                LOG.info('About to delete tags')
                del value["Properties"]["Tags"]
    write_json_file(cfn, cfn_output_template)
