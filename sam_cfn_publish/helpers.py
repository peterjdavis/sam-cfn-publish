import os
from os.path import basename
import tempfile
import shutil
import logging

from cfn_flip import load_json, to_json, dump_json, to_yaml, dump_yaml, load_yaml

LOG = logging.getLogger(__name__)

def get_cfn_parameter(search_item) -> any:
    for cfn_parameter in cfn_parameters:
        if cfn_parameter == search_item:
            item = cfn_parameters[cfn_parameter]
            return item

def resolve_element(cfn, element):
    if 'Ref' in element:
        item = get_cfn_parameter(element['Ref'])
        return item
    elif 'Fn::Sub' in element:
        items = element['Fn::Sub'].split('${')
        item = ''
        for sub_item in items:
            split_sub_item = sub_item.split('}')
            if len(split_sub_item) == 1:
                item = item + split_sub_item[0]
            else:
                item = item + \
                    get_cfn_parameter(split_sub_item[0]) + split_sub_item[1]
        return item
    else:
        return element

def get_filename_from_path(path):
    return basename(path)

def get_extension_from_path(path):
    return path.split('.')[-1]

def check_create_folder(path):
    if not os.path.exists(path):
        os.makedirs(path) 

def get_lambda_source(path, handler, spaces, working_folder):
    shutil.unpack_archive(path, working_folder, 'zip')
    handler_prefix = handler.split('.')[0]
    lambda_source_file = f'{working_folder}/{handler_prefix}.py'
    function_content = ''

    with open(lambda_source_file, mode='r') as f:
        for line in f:
            function_content += ' ' * spaces + line
        function_content += '\n'
    return function_content

def get_code(source_bucket, source_key, spaces, working_folder, s3_client):
    filename = get_filename_from_path(source_key)
    local_zip_file = f'{working_folder}/{filename}'
    LOG.debug('About to download source from source_bucket: %s', source_bucket)
    LOG.debug('About to download source from source_key: %s', source_key)
    LOG.debug('About to write source zip to: %s', local_zip_file)
    s3_client.download_file(
        source_bucket, source_key, local_zip_file)

    return get_lambda_source(local_zip_file, 'index.lambda_handler', spaces, working_folder)

def get_bucket_from_code_uri(code_uri):
    bucket = code_uri.split('/')[2]
    return bucket

def get_key_from_code_uri(code_uri):
    key_parts = code_uri.split('/')

    key = ''
    for i in range(3, len(key_parts)):
        if key == '':
            key = key_parts[i]
        else:
            key = key + '/' + key_parts[i]
    return key
 
def count_spaces(line):
    spaces = 0
    for character in line:
        if character == ' ':
            spaces += 1
        else:
            break
    return spaces

def write_json_file(cfn, cfn_output_template):
    """Convert ain memory cfn template to json file"""
    with open(cfn_output_template, 'w') as f:
        f.write(to_json(dump_json(cfn), clean_up=True))

def write_yaml_file(cfn, cfn_output_template):
    """Convert a in memory cfn template to yaml file"""
    with open(cfn_output_template, 'w') as f:
        f.write(to_yaml(dump_yaml(cfn), clean_up=True))

def convert_to_yaml(cfn_input_template, cfn_output_template):
    """Convert a json based cfn template on the filesystem to yaml"""
    with open(cfn_input_template) as f:
        str_cfn = f.read()
        cfn = load_json(str_cfn)
        write_yaml_file(cfn, cfn_output_template)

def get_temp_folder():
    """Create a temporary folder for the working files"""    
    temp_path = tempfile.mkdtemp()
    return temp_path
    