import logging

from . import helpers 

LOG = logging.getLogger(__name__)

LEVEL_0_SPACES = 0 

def inline_lambda_functions(output_format, cfn_input_template, cfn_output_template, working_folder, s3_client):
    with open(cfn_output_template, mode='w') as wf:
        with open(cfn_input_template, mode='r') as rf:
            current_level = 0
            level_1_spaces, level_2_spaces, level_3_spaces, level_4_spaces = 0, 0, 0, 0

            for line in rf:
                line_spaces = helpers.count_spaces(line)
                if line_spaces == LEVEL_0_SPACES:
                    level_0_element = line.strip()
                    wf.writelines(line)
                elif (line_spaces > LEVEL_0_SPACES and current_level == 0) or \
                    (line_spaces == level_1_spaces and current_level >= 1):
                    level_1_spaces = line_spaces
                    level_1_element = line.strip()
                    current_level = 1
                    in_function = False
                    in_metadata = False
                    inline_function = False
                    in_code = False
                    source_bucket = ''
                    source_key = ''
                    handler = ''
                    wf.writelines(line)
                elif (line_spaces > level_1_spaces and current_level == 1) or \
                    (line_spaces == level_2_spaces and current_level >= 2):
                    level_2_spaces = line_spaces
                    level_2_element = line.strip()
                    current_level = 2
                    if level_2_element.startswith('Type: AWS::Lambda::Function') or \
                        level_2_element.startswith('Type: AWS::Serverless::Function'):
                        in_function = True
                    if level_2_element.startswith('Metadata:'):
                        in_metadata = True
                    wf.writelines(line)
                elif (line_spaces > level_2_spaces and current_level == 2) or \
                    (line_spaces == level_3_spaces and current_level >= 3):
                    level_3_spaces = line_spaces
                    level_3_element = line.strip()
                    current_level = 3
                    if in_metadata and in_function:
                        if level_3_element.startswith('InlineSAMFunction: true'):
                            inline_function = True
                    if output_format == 'SAM':
                        if inline_function and in_function and level_3_element.startswith('CodeUri:' ):
                            in_code = True
                            source_bucket = helpers.get_bucket_from_code_uri(level_3_element)
                            source_key = helpers.get_key_from_code_uri(level_3_element)
                        if inline_function and in_function and level_3_element.startswith('Handler: '):
                            handler = level_3_element

                        if source_bucket != '' and source_key != '' and handler != '':
                            wf.writelines(' ' * level_3_spaces + 'InlineCode: |\n')
                            wf.writelines(helpers.get_code(source_bucket, source_key, level_3_spaces + 2, working_folder, s3_client))
                            wf.writelines(' ' * level_3_spaces + handler + '\n')
                            source_bucket = ''
                            source_key = ''
                            handler = ''
                        elif not (inline_function and level_3_element.startswith('CodeUri:')): # don't write the CodeUri element if inlining
                        # else:
                            wf.writelines(line)
                    elif output_format == 'CFN':
                        if inline_function and in_function and level_3_element.startswith('Code:' ):
                            in_code = True
                        if inline_function and in_function and level_3_element.startswith('Handler: '):
                            handler = level_3_element
                        
                        if source_bucket != '' and source_key != '' and handler != '':
                            wf.writelines(' ' * level_4_spaces + 'ZipFile: |\n')
                            wf.writelines(helpers.get_code(source_bucket, source_key, level_4_spaces + 2, working_folder, s3_client))
                            wf.writelines(' ' * level_3_spaces + handler + '\n')
                            source_bucket = ''
                            source_key = ''
                            handler = ''
                        else:
                            wf.writelines(line)
                elif (line_spaces > level_3_spaces and current_level == 3) or \
                    (line_spaces == level_4_spaces and current_level >= 4):
                    level_4_spaces = line_spaces
                    level_4_element = line.strip()
                    current_level = 4
                    if in_code and level_4_element.startswith('S3Bucket: '):
                        LOG.debug('source_bucket before processing: %s', level_4_element)
                        source_bucket = level_4_element.replace('S3Bucket:', '').strip(' ')
                    elif in_code and level_4_element.startswith('S3Key: '):
                        source_key = level_4_element.replace('S3Key:', '').strip(' ')
                    else:
                        wf.writelines(line)

                    if source_bucket != '' and source_key != '' and handler != '':
                        wf.writelines(' ' * level_4_spaces + 'ZipFile: |\n')
                        wf.writelines(helpers.get_code(source_bucket, source_key, level_4_spaces + 2, working_folder, s3_client))
                        wf.writelines(' ' * level_3_spaces + handler + '\n')
                        source_bucket = ''
                        source_key = ''
                        handler = ''
                else:
                    wf.writelines(line)
