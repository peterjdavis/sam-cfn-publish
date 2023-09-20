import logging
import json

from cfn_flip import load_json, load_yaml
from . import helpers

LOG = logging.getLogger(__name__)

def process_lambda(cfn, key, value, target_asset_bucket, target_prefix, target_asset_folder, lambda_path, s3_client):
    LOG.info('Processing Lambda: %s', key)
    if 'S3Bucket' in value['Properties']['Code']:
        if not('InlineSAMFunction' in value["Metadata"] and value["Metadata"]['InlineSAMFunction'] == True):
            source_bucket = helpers.resolve_element(
                cfn, value['Properties']['Code']['S3Bucket'])
            source_key = helpers.resolve_element(
                cfn, value['Properties']['Code']['S3Key'])
            target_local_path = f'{target_asset_folder}/{lambda_path}'
            helpers.check_create_folder(target_local_path)
            filename = helpers.get_filename_from_path(source_key)
            s3_client.download_file(
                source_bucket, source_key, f'{target_local_path}/{filename}')
            value['Properties']['Code']['S3Bucket'] = {
                'Ref': target_asset_bucket}
            value['Properties']['Code']['S3Key'] = {
                'Fn::Sub': f'{target_prefix}/{lambda_path}/{filename}'.replace('//', '/').strip('/')}
        else:
            LOG.info('Code is marked for inlining InlineSAMFunction Metadata: %s', value["Metadata"]['InlineSAMFunction'])
    else:
        LOG.info('Code is not referenced from an S3 Bucket')


def process_function(cfn, key, value, target_asset_bucket, target_prefix, target_asset_folder, lambda_path, s3_client, output_format):
    LOG.info('Processing Serverless Function: %s', key)
    if 'CodeUri' in value['Properties']:
        if not('InlineSAMFunction' in value["Metadata"] and value["Metadata"]['InlineSAMFunction'] == True):
            if output_format == 'SAM':
                code_uri = helpers.resolve_element(
                    cfn, value['Properties']['CodeUri'])
                source_bucket = helpers.get_bucket_from_code_uri(code_uri)
                source_key = helpers.get_key_from_code_uri(code_uri)
            elif output_format == 'CFN':
                source_bucket = helpers.resolve_element(
                    cfn, value['Properties']['Code']['S3Bucket'])
                source_key = helpers.resolve_element(
                    cfn, value['Properties']['Code']['S3Key'])
            target_local_path = f'{target_asset_folder}/{lambda_path}'
            helpers.check_create_folder(target_local_path)
            filename = helpers.get_filename_from_path(source_key)
            s3_client.download_file(
                source_bucket, source_key, f'{target_local_path}/{filename}')
            if output_format == 'SAM':
                value['Properties'].pop('CodeUri')
                value['Properties']['CodeUri'] = {}
                value['Properties']['CodeUri']['Bucket'] = {
                    'Ref': target_asset_bucket
                    }
                value['Properties']['CodeUri']['Key'] = {
                    'Fn::Sub': f'{target_prefix}/{lambda_path}/{filename}'.replace('//', '/').strip('/')
                    }
            elif output_format == 'CFN':
                value['Properties']['Code']['S3Bucket'] = {
                    'Ref': target_asset_bucket
                    }
                value['Properties']['Code']['S3Key'] = {
                    'Fn::Sub': f'{target_prefix}/{lambda_path}/{filename}'.replace('//', '/').strip('/')
                    }
        else:
            LOG.info('Code is marked for inlining InlineSAMFunction Metadata: %s', value["Metadata"]['InlineSAMFunction'])
    else:
        LOG.info('Code is not referenced from an S3 Bucket')

def process_layer(cfn, key, value, target_asset_bucket, target_prefix, target_asset_folder, layer_path, s3_client):
    LOG.info('Processing Layer: %s', key)
    source_bucket = helpers.resolve_element(
        cfn, value['Properties']['Content']['S3Bucket'])
    source_key = helpers.resolve_element(
        cfn, value['Properties']['Content']['S3Key'])
    target_local_path = f'{target_asset_folder}/{layer_path}'
    helpers.check_create_folder(target_local_path)
    filename = helpers.get_filename_from_path(source_key)
    s3_client.download_file(
        source_bucket, source_key, f'{target_local_path}/{filename}')
    value['Properties']['Content']['S3Bucket'] = {
        'Ref': target_asset_bucket}
    value['Properties']['Content']['S3Key'] = {
        'Fn::Sub': f'{target_prefix}/{layer_path}/{filename}'.replace('//', '/').strip('/')}

def process_statemachine(cfn, key, value, target_asset_bucket, target_prefix, target_asset_folder, statemachine_path, s3_client):
    print('Processing Satemachine: %s', key)
    source_bucket = helpers.resolve_element(
        cfn, value['Properties']['DefinitionS3Location']['Bucket'])
    source_key = helpers.resolve_element(
        cfn, value['Properties']['DefinitionS3Location']['Key'])
    target_local_path = f'{target_asset_folder}/{statemachine_path}/'
    helpers.check_create_folder(target_local_path)
    filename = helpers.get_filename_from_path(source_key)
    s3_client.download_file(
        source_bucket, source_key, f'{target_local_path}/{filename}')
    value['Properties']['DefinitionS3Location']['Bucket'] = {
        'Ref': target_asset_bucket}
    value['Properties']['DefinitionS3Location']['Key'] = {
        'Fn::Sub': f'{target_prefix}/{statemachine_path}/{filename}'.replace('//', '/').strip('/')}

def move_assets(output_format, cfn_input_template, cfn_output_template, target_asset_bucket, target_prefix, target_asset_folder, lambda_path, layer_path, statemachine_path, s3_client):
    with open(cfn_input_template) as f:
        str_cfn = f.read()

        template_extension = helpers.get_extension_from_path(cfn_input_template)
        if template_extension == 'yaml':
            cfn = load_yaml(str_cfn)
        else:
            cfn = load_json(str_cfn)
        resources = cfn["Resources"]

        for key, value in resources.items():
            if value["Type"] == "AWS::Lambda::Function":
                process_lambda(cfn, key, value, target_asset_bucket, target_prefix, target_asset_folder, lambda_path, s3_client)
            if value["Type"] == "AWS::Serverless::Function":
                process_function(cfn, key, value, target_asset_bucket, target_prefix, target_asset_folder, lambda_path, s3_client, output_format)
            if value["Type"] == "AWS::Lambda::LayerVersion":
                process_layer(cfn, key, value, target_asset_bucket, target_prefix, target_asset_folder, layer_path, s3_client)
            if value["Type"] == "AWS::StepFunctions::StateMachine":
                process_statemachine(cfn, key, value, target_asset_bucket, target_prefix, target_asset_folder, statemachine_path, s3_client)

    helpers.write_json_file(cfn, cfn_output_template)

