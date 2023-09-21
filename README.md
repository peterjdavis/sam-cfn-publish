# Overview
If you author an [AWS Serverless Application Model (SAM)](https://aws.amazon.com/serverless/sam/) template you may wish to publish this as an [AWS CloudFormation](https://docs.aws.amazon.com/cloudformation/index.html) template to allow the user to deploy the solution from the console and remove the need for the user to install the [AWS SAM CLI](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html).

Much of this can be achieved by using commands such as `sam package` to package your template and upload the assets to S3 and [aws-sam-translator](https://pypi.org/project/aws-sam-translator/) to transform the SAM template into a AWS CloudFormation template.  sam-cfn-publish allows you to further transform your CloudFormation template in three ways:
* Inlining of [AWS Lambda](https://docs.aws.amazon.com/lambda/latest/dg/welcome.html) functions into the CloudFormation template to allow the user to the see the functions in the main template
* Control of the buckets where the assets are stored e.g. [AWS Step Functions](https://aws.amazon.com/step-functions/) and [Lambda Layers](https://docs.aws.amazon.com/lambda/latest/dg/configuration-layers.html).  The can be useful if you would like to deploy the assets to a separate AWS account which may have publicly accessible buckets available specifically for sharing assets with users.
* Removes the metadata and tags that are added to resources when converted using [aws-sam-translator](https://pypi.org/project/aws-sam-translator/)

# Unsupported Resoruce Types
* AWS::Serverless::GraphQLApi

# Command Line Arguments
  `--output-format` - Create the output as an untransformed SAM Template, useful for moving assets and inlining functions (experimental)

  `--working-folder WORKING_FOLDER` - Working folder for the input and output files.  Normally a local temp folder. (optional)
  
  `--cfn-input-template CFN_INPUT_TEMPLATE` - Name of JSON template to transform [default: template.json].  Normally the output from `sam package` command
   
   `--cfn-output-template CFN_OUTPUT_TEMPLATE` - Name of YAML template to output [default: template.yaml].

  `--target-asset-folder TARGET_ASSET_FOLDER` - Local folder the assets should be stored [default: ./Assets/].

  `--lambda-folder LAMBDA_FOLDER` - Location the lambda assets should be stored, this is appended to the target-asset-folder [default: lambda].

  `--layer-folder LAYER_FOLDER` - Location the layer assets should be stored, this is appended to the target-asset-folder [default: layer].

  `--statemachine-folder STATEMACHINE_FOLDER` - Location the statemachine assets should be stored, this is appended to the target-asset-folder [default: statemachine].

  `--target-asset-bucket TARGET_ASSET_BUCKET` - Bucket the assets will be stored in.  This is used update the references in the CloudFormation template.  The assets are not actually copied to this bucket.  Typically this will be done using an `aws s3 sync` command

  `--target-prefix TARGET_PREFIX` - Prefix that should be applied to the updated references in the CloudFormation template if the assets are not going to uploaded to the root [default: ''].

  `--move-assets` - Should references to the assets in the CloudFormation template be updated to a different bucket [default: False]

  `--tidy-tags-metadata` - Should SAM tags and metadata be tidied up [Default: True]?

  `--add-layout-gaps` - Should a new line be added between each resource for readability [Default: True]?

  `--debug` - Enables debug logging [Default: False]

  `--verbose` - Enables verbose logging [Default: True]

# Inlining Lambda Functions
To inline a Lambda function you should include a metadata element `InlineSAMFunction: true` in the AWS::Serverless::Function resource as shown below

```YAML
  SampleInlineFunction:
    Type: AWS::Serverless::Function
    Metadata:
      InlineSAMFunction: true
    Properties:
      CodeUri: src/lambda/testFunction
      Handler: index.lambda_handler
      Runtime: python3.9
      Layers:
        - !Ref SampleLayer
```
When processed by sam-cfn-publish the associated code will be included in the output CloudFormation template.  If the Lambda function relies on non standard packages these should be included in a Layer and referenced from the resource or the resource left as a reference in S3.

# Example uses
Assuming that you have a SAM Template in the current folder e.g. https://github.com/peterjdavis/sam-cfn-publish/blob/main/samples/sam-template.yaml then the following commands could be used to transform this to the CloudFormation template shown at https://github.com/peterjdavis/sam-cfn-publish/blob/main/samples/cfn-template.yaml
```bash
#!/bin/bash

# Create a virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install sam-cfn-publish
pip3 install sam-cfn-publish

# Get some environment variables
AWSAccount=$(aws sts get-caller-identity --query Account --output text)
AWSRegion=$(aws configure get region)
export tmpCFNDir=$(mktemp -d)

# Build the SAM project
sam build -t sam-template.yaml

# Check to make sure the bucket for the SAM assets exists
if aws s3api head-bucket --bucket sam-${AWSAccount}-${AWSRegion} 2>/dev/null; \
    then echo Bucket sam-${AWSAccount}-${AWSRegion} exists; \
    else echo Creating bucket sam-${AWSAccount}-${AWSRegion} && \
        aws s3 mb s3://sam-${AWSAccount}-${AWSRegion} --region ${AWSRegion} ; \
    fi

# Package the SAM template so the assets are available in the s3 bucket and teh updated template is available
sam package -t sam-template.yaml \
            --output-template-file ${tmpCFNDir}/sam-template.tmp.yaml \
            --s3-bucket sam-${AWSAccount}-${AWSRegion} 

# Update the CloudFormation template so lambda's with an InlineSAMFunction: true metadata tag are inlined
# assets are referenced from a parameter call AssetBucket and the layer and lambda are referenced from a default prefix
sam-cfn-publish \
    --working-folder ${tmpCFNDir} \
    --cfn-input-template ${tmpCFNDir}/sam-template.tmp.yaml \
    --cfn-output-template cfn-template.yaml \
    --target-asset-folder assets/cfn \
    --target-asset-bucket AssetBucket \
    --move-assets \
    --verbose

# Tidy up the temporary folder
rm -rf ${tmpCFNDir}
```