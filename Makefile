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
	python3 -m build
.PHONY : test
test : init
	cd samples
	sam build -t sam-template.yaml
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

	sam package --output-template-file ${tmpCFNDir}/cfn1-template-.tmp.yaml --s3-bucket sam-${awsAccount}-${awsRegion}
	
	python3 sam-translate.py \
		--template-file=${tmpCFNDir}/template-cfn1.tmp.yaml \
		--output-template=${tmpCFNDir}/template-cfn2.tmp.json