import os
from os.path import basename
import shutil
import logging

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
    # path_parts = path.split('/')
    # return path_parts[len(path_parts) - 1]
    return basename(path)

def check_create_folder(path):
    if not os.path.exists(path):
        os.makedirs(path) 

def get_lambda_source(path, handler, spaces, working_folder):
    shutil.unpack_archive(path, working_folder, 'zip')
    handler_prefix = handler.split('.')[0]
    lambda_source_file = working_folder + '/' + handler_prefix + '.py'
    # os.remove(path)
    function_content = ''

    with open(lambda_source_file, mode='r') as f:
        for line in f:
            function_content += ' ' * spaces + line
        function_content += '\n'
    return function_content

def get_code(source_bucket, source_key, spaces, working_folder, target_asset_folder, lambda_folder, s3_client):
    filename = get_filename_from_path(source_key)
    # LOG.info('Source Bucket: %s', source_bucket)
    # LOG.info('Source Key: %s', source_key)
    # LOG.info('target_asset_folder: %s', target_asset_folder)
    # LOG.info('lambda_folder: %s', lambda_folder)
    # LOG.info('filename: %s', filename)

    local_zip_file = f'{working_folder}/{filename}'
    s3_client.download_file(
        source_bucket, source_key, local_zip_file)

    return get_lambda_source(local_zip_file, 'index.lambda_handler', spaces, working_folder)

def count_spaces(line):
    spaces = 0
    for character in line:
        if character == ' ':
            spaces += 1
        else:
            break
    return spaces
