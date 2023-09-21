import logging
import cfn_flip
from . import helpers

LOG = logging.getLogger(__name__)
LEVEL_0_SPACES = 0 

def tidy_tags(cfn_input_template, cfn_output_template, working_folder):
    with open(cfn_input_template) as f:
        str_cfn = f.read()

    cfn = cfn_flip.load_json(str_cfn)
    resources = cfn["Resources"]

    for key, value in resources.items():
        LOG.info('Tidying tags in %s', key)
        if "Properties" in value:
            if "Tags" in value["Properties"]:
                tags = value["Properties"]["Tags"]
                i = 0
                for tag in tags:
                    if 'Key' in tag and tag['Key'] == 'lambda:createdBy' and tag['Value'] == 'SAM':
                        del value["Properties"]["Tags"][i]
                        i = i + 1
                    if 'httpapi:createdBy' in tag and tag['httpapi:createdBy'] == 'SAM':
                        del value["Properties"]["Tags"][i]
                        i = i + 1
                if value["Properties"]["Tags"] == []:
                    del value["Properties"]["Tags"]
    helpers.write_json_file(cfn, cfn_output_template)

def tidy_metadata(cfn_input_template, cfn_output_template, add_layout_gaps):
    """Process the Yaml document to remove SAM metadata"""
    with open(cfn_output_template, mode='w') as wf:
        with open(cfn_input_template, mode='r') as rf:
            current_level = 0
            level_1_spaces, level_2_spaces, level_3_spaces = 0, 0, 0

            for line in rf:
                if line.strip() != '':
                    line_spaces = helpers.count_spaces(line)
                    if line_spaces == LEVEL_0_SPACES:
                        level_0_element = line.strip()
                        if add_layout_gaps and current_level != 0:
                            wf.writelines('\n')
                        current_level = 0
                        wf.writelines(line)
                    elif (line_spaces > LEVEL_0_SPACES and current_level == 0) or \
                        (line_spaces == level_1_spaces and current_level >= 1):
                        level_1_spaces = line_spaces
                        level_1_element = line.strip()
                        if add_layout_gaps and current_level != 0:
                            wf.writelines('\n')
                        current_level = 1
                        in_metadata = False
                        other_metadata_found = False
                        wf.writelines(line)
                    elif (line_spaces > level_1_spaces and current_level == 1) or \
                        (line_spaces == level_2_spaces and current_level >= 2):
                        level_2_spaces = line_spaces
                        level_2_element = line.strip()
                        current_level = 2
                        if level_2_element.startswith('Metadata:') and not in_metadata:
                            in_metadata = True
                        else:
                            in_metadata = False
                            wf.writelines(line)
                    elif (line_spaces > level_2_spaces and current_level == 2) or \
                        (line_spaces == level_3_spaces and current_level >= 3):
                        level_3_spaces = line_spaces
                        level_3_element = line.strip()
                        current_level = 3
                        if in_metadata:
                            if level_3_element.startswith('InlineSAMFunction: true') \
                                or level_3_element.startswith('SamResourceId:'):
                                LOG.info('Tidying metadata %s - %s', level_1_element, level_3_element)
                            else:
                                if in_metadata and not other_metadata_found:
                                    wf.writelines(' ' * level_2_spaces + level_2_element + '\n')
                                    other_metadata_found = True
                                wf.writelines(line)
                        else:
                            wf.writelines(line)
                    else:
                        wf.writelines(line)
                else:
                    wf.writelines('\n')
