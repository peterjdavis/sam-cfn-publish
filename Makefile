SHELL := /bin/bash
.ONESHELL:

include .env
export

.PHONY : init
init :
	python3 -m venv .venv
	source .venv/bin/activate
	pip3 install -r requirements.txt

.PHONY : package
package :
	rm -rf dist/
	python3 -m build
	python3 -m twine upload --skip-existing --repository testpypi dist/*

.PHONY : package-live
package-live : package
	python3 -m twine upload dist/*

.PHONY : test
test : 
	source .venv/bin/activate
	pip3 install --force-reinstall dist/sam_publish-0.1.0-py3-none-any.whl 
	sam build -t samples/sam-template.yaml
	$(eval awsAccount := $(shell aws sts get-caller-identity --query Account --output text))
	# $(eval tmpCFNDir := $(shell mktemp -d))
	$(eval tmpCFNDir := .tmp)
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

	sam package -t samples/sam-template.yaml --output-template-file ${tmpCFNDir}/cfn1-template.tmp.yaml --s3-bucket sam-${awsAccount}-${awsRegion}

	python3 -m sam_publish \
		--working_folder ${tmpCFNDir} \
    	--cfn-input-template ${tmpCFNDir}/cfn1-template.tmp.yaml \
    	--cfn-output-template samples/cfn-template.yaml \
    	--target-asset-folder samples/assets/cfn \
		--target-asset-bucket AssetBucket \
		--move-assets \
		--verbose