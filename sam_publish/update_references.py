import boto3
from cfn_flip import load_json

def process_template():
    with open(CFN_INPUT_TEMPLATE) as f:
        str_cfn = f.read()

        cfn = load_json(str_cfn)
        resources = cfn["Resources"]

        for key, value in resources.items():
            # if value["Type"] == "AWS::Lambda::Function":
            #     print(f'Processing: {key}')
            #     if 'S3Bucket' in value['Properties']['Code']:
            #         source_bucket = resolve_element(
            #             cfn, value['Properties']['Code']['S3Bucket'])
            #         source_key = resolve_element(
            #             cfn, value['Properties']['Code']['S3Key'])
            #         target_sub_path = '/lambda/'
            #         filename = get_filename_from_path(source_key)
            #         handler = value['Properties']['Handler']
            #         s3_client.download_file(
            #             source_bucket, source_key, TARGET_ASSET_FOLDER + target_sub_path + filename)
            #         if 'InlineSAMFunction' in value["Metadata"] and value["Metadata"]['InlineSAMFunction'] == True:
            #             print(f'going to inine {key}')
            #             lambda_source = get_lambda_source(
            #                 TARGET_ASSET_FOLDER + target_sub_path + filename, handler)
            #             value['Properties']['Code']['ZipFile'] = lambda_source
            #             del value['Properties']['Code']['S3Bucket']
            #             del value['Properties']['Code']['S3Key']
            #         else:
            #             value['Properties']['Code']['S3Bucket'] = {
            #                 'Ref': 'EEAssetsBucket'}
            #             value['Properties']['Code']['S3Key'] = {
            #                 'Fn::Sub': 'modules/${EEModuleId}/v${EEModuleVersion}/cfn' + target_sub_path + source_key}
            #     else:
            #         print(f'Code is not referenced from an S3 Bucket')
            if value["Type"] == "AWS::Lambda::LayerVersion":
                print('Processing: ' + key)
                source_bucket = resolve_element(
                    cfn, value['Properties']['Content']['S3Bucket'])
                source_key = resolve_element(
                    cfn, value['Properties']['Content']['S3Key'])
                target_sub_path = '/layer/'
                filename = get_filename_from_path(source_key)
                s3_client.download_file(
                    source_bucket, source_key, TARGET_ASSET_FOLDER + target_sub_path + filename)
                value['Properties']['Content']['S3Bucket'] = {
                    'Ref': 'AssetBucket'}
                value['Properties']['Content']['S3Key'] = {
                    'Fn::Sub': target_sub_path[1:] + source_key}
            elif value["Type"] == "AWS::StepFunctions::StateMachine":
                print('Processing: ' + key)
                source_bucket = resolve_element(
                    cfn, value['Properties']['DefinitionS3Location']['Bucket'])
                source_key = resolve_element(
                    cfn, value['Properties']['DefinitionS3Location']['Key'])
                target_sub_path = '/statemachine/'
                filename = get_filename_from_path(source_key)
                s3_client.download_file(
                    source_bucket, source_key, TARGET_ASSET_FOLDER + target_sub_path + filename)
                value['Properties']['DefinitionS3Location']['Bucket'] = {
                    'Ref': 'EEAssetsBucket'}
                value['Properties']['DefinitionS3Location']['Key'] = {
                    'Fn::Sub': 'modules/${EEModuleId}/v${EEModuleVersion}/cfn' + target_sub_path + source_key}
