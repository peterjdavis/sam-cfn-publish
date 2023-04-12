#!/bin/bash

inputTemplate=/Users/pjdavis/Dev/CodeCommitReposV2/pjdavis+lza-no-ct-4/aws-accelerator-config/sam/template.yaml
outputTemplate=/Users/pjdavis/Dev/CodeCommitReposV2/pjdavis+lza-no-ct-4/aws-accelerator-config/sam/cfnTemplate.yaml
awsRegion=eu-west-1
# python3 -m venv .venv
# source .venv/bin/activate
# pip3 install -r requirements.txt

source .venv/bin/activate
pip3 install git+https://github.com/peterjdavis/sam-publish.git@initial-version
sam build -t ${inputTemplate}
awsAccount=$(aws sts get-caller-identity --query Account --output text)
tmpCFNDir=$(mktemp -d)
tmpCFNDir=.tmp
if aws s3api head-bucket --bucket sam-${awsAccount}-${awsRegion} 2>/dev/null; \
    then echo Bucket sam-${awsAccount}-${awsRegion} exists; \
    else echo Creating bucket sam-${awsAccount}-${awsRegion} && \
        aws s3 mb s3://sam-${awsAccount}-${awsRegion} --region ${awsRegion} ; \
    fi

if test -e ${tmpCFNDir}; \
    then echo ${tmpCFNDir} folder exists; \
    else echo Creating ${tmpCFNDir} folder && \
        mkdir ${tmpCFNDir};
    fi

sam package -t ${inputTemplate} --output-template-file ${tmpCFNDir}/cfn1-template.tmp.yaml --s3-bucket sam-${awsAccount}-${awsRegion}

python3 -m sam_publish \
    --working_folder ${tmpCFNDir} \
    --cfn-input-template ${tmpCFNDir}/cfn1-template.tmp.yaml \
    --cfn-output-template ${outputTemplate} \
    --target-asset-folder samples/assets/cfn \
    --target-asset-bucket AssetBucket \
    --verbose