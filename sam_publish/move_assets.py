from cfn_flip import load_json, to_yaml, dump_yaml
from .helpers import resolve_element, get_filename_from_path, check_create_folder
import logging

LOG = logging.getLogger(__name__)

def process_lambda(cfn, key, value, target_assets_bucket, target_prefix, target_asset_folder, lambda_path, s3_client):
    LOG.info('Processing Lambda: %s', key)
    if 'S3Bucket' in value['Properties']['Code']:
        if not('InlineSAMFunction' in value["Metadata"] and value["Metadata"]['InlineSAMFunction'] == True):
            source_bucket = resolve_element(
                cfn, value['Properties']['Code']['S3Bucket'])
            source_key = resolve_element(
                cfn, value['Properties']['Code']['S3Key'])
            target_path = f'{target_asset_folder}/{lambda_path}/'
            check_create_folder(target_path)
            filename = get_filename_from_path(source_key)
            # handler = value['Properties']['Handler']
            s3_client.download_file(
                source_bucket, source_key, target_path + filename)
            value['Properties']['Code']['S3Bucket'] = {
                'Ref': target_assets_bucket}
            value['Properties']['Code']['S3Key'] = {
                'Fn::Sub': target_prefix + target_path + source_key}
    else:
        print(f'Code is not referenced from an S3 Bucket')

def process_layer(cfn, key, value, target_assets_bucket, target_prefix, target_asset_folder, layer_path, s3_client):
    LOG.info('Processing Layer: %s', key)
    source_bucket = resolve_element(
        cfn, value['Properties']['Content']['S3Bucket'])
    source_key = resolve_element(
        cfn, value['Properties']['Content']['S3Key'])
    target_local_path = f'{target_asset_folder}/{layer_path}'
    check_create_folder(target_local_path)
    filename = get_filename_from_path(source_key)
    s3_client.download_file(
        source_bucket, source_key, f'{target_local_path}/{filename}')
    value['Properties']['Content']['S3Bucket'] = {
        'Ref': target_assets_bucket}
    value['Properties']['Content']['S3Key'] = {
        'Fn::Sub': f'{target_prefix}/{layer_path}/{source_key}'.strip('/')}

def process_statemachine(cfn, key, value, target_assets_bucket, target_prefix, target_asset_folder, statemachine_path, s3_client):
    print('Processing Satemachine: %s', key)
    source_bucket = resolve_element(
        cfn, value['Properties']['DefinitionS3Location']['Bucket'])
    source_key = resolve_element(
        cfn, value['Properties']['DefinitionS3Location']['Key'])
    target_sub_path = f'{target_asset_folder}/{statemachine_path}/'
    filename = get_filename_from_path(source_key)
    s3_client.download_file(
        source_bucket, source_key, target_asset_folder + target_sub_path + filename)
    value['Properties']['DefinitionS3Location']['Bucket'] = {
        'Ref': target_assets_bucket}
    value['Properties']['DefinitionS3Location']['Key'] = {
        'Fn::Sub': target_prefix + target_sub_path + source_key}

def move_assets(cfn_input_template, cfn_output_template, target_assets_bucket, target_prefix, target_asset_folder, lambda_path, layer_path, statemachine_path, s3_client):
    with open(cfn_input_template) as f:
        str_cfn = f.read()

        cfn = load_json(str_cfn)
        resources = cfn["Resources"]

        for key, value in resources.items():
            if value["Type"] == "AWS::Lambda::Function":
                process_lambda(cfn, key, value, target_assets_bucket, target_prefix, target_asset_folder, lambda_path, s3_client)
            if value["Type"] == "AWS::Lambda::LayerVersion":
                process_layer(cfn, key, value, target_assets_bucket, target_prefix, target_asset_folder, layer_path, s3_client)
            elif value["Type"] == "AWS::StepFunctions::StateMachine":
                process_statemachine(cfn, key, value, target_assets_bucket, target_prefix, target_asset_folder, statemachine_path, s3_client)

    write_yaml_file(cfn, cfn_output_template)

def write_yaml_file(cfn, cfn_output_template):
    with open(cfn_output_template, 'w') as f:
        f.write(to_yaml(dump_yaml(cfn), clean_up=True))

def convert_to_yaml(cfn_input_template, cfn_output_template):
    with open(cfn_input_template) as f:
        str_cfn = f.read()

        cfn = load_json(str_cfn)

        write_yaml_file(cfn, cfn_output_template)