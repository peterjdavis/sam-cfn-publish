#!/bin/bash

rm -rf .venv .aws-sam

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

# Update the CloudFormation tempalte so lambda's with an InlineSAMFunction: true metadata tag are inlined
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