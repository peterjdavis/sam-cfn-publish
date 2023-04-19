import logging
import json

from cfn_flip import load_json
from .helpers import resolve_element, get_filename_from_path, check_create_folder, write_json_file


LOG = logging.getLogger(__name__)

def process_lambda(cfn, key, value, target_assets_bucket, target_prefix, target_asset_folder, lambda_path, s3_client):
    LOG.info('Processing Lambda: %s', key)
    LOG.info('Value is: %s', json.dumps(value))
    if 'S3Bucket' in value['Properties']['Code']:
        if not('InlineSAMFunction' in value["Metadata"] and value["Metadata"]['InlineSAMFunction'] == True):
            source_bucket = resolve_element(
                cfn, value['Properties']['Code']['S3Bucket'])
            source_key = resolve_element(
                cfn, value['Properties']['Code']['S3Key'])
            target_local_path = f'{target_asset_folder}/{lambda_path}'
            check_create_folder(target_local_path)
            filename = get_filename_from_path(source_key)
            s3_client.download_file(
                source_bucket, source_key, f'{target_local_path}/{filename}')
            value['Properties']['Code']['S3Bucket'] = {
                'Ref': target_assets_bucket}
            value['Properties']['Code']['S3Key'] = {
                'Fn::Sub': f'{target_prefix}/{lambda_path}/{source_key}'.strip('/')}
        else:
            LOG.info('Code is marked for inlining InlineSAMFunction Metadata: %s', value["Metadata"]['InlineSAMFunction'])
    else:
        LOG.info('Code is not referenced from an S3 Bucket')

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
    target_local_path = f'{target_asset_folder}/{statemachine_path}/'
    check_create_folder(target_local_path)
    filename = get_filename_from_path(source_key)
    s3_client.download_file(
        source_bucket, source_key, f'{target_local_path}/{filename}')
    value['Properties']['DefinitionS3Location']['Bucket'] = {
        'Ref': target_assets_bucket}
    value['Properties']['DefinitionS3Location']['Key'] = {
        'Fn::Sub': f'{target_prefix}/{statemachine_path}/{source_key}'.strip('/')}

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

    write_json_file(cfn, cfn_output_template)

