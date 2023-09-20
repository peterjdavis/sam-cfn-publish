SHELL := /bin/bash
.ONESHELL:

include .env
export

.PHONY : clean
clean :
	rm -rf dist/ .venv/ .tmp/

.PHONY : init
init :
	python3 -m venv .venv
	source .venv/bin/activate
	pip3 install -r requirements.txt

.PHONY : build
build :
	python3 -m build

.PHONY : deploy-test
deploy-test : build
	python3 -m twine upload --skip-existing --repository testpypi dist/*

.PHONY : deploy-live
deploy-live : deploy
	python3 -m twine upload dist/*

.PHONY : package-template
package-template : build
	source .venv/bin/activate
	pip3 install --force-reinstall dist/sam_cfn_publish-0.2.3-py3-none-any.whl 
	# pip3 install dist/sam_cfn_publish-0.2.3-py3-none-any.whl 
	sam build -t samples/sam-template.yaml
	$(eval awsAccount := $(shell aws sts get-caller-identity --query Account --output text))
	# $(eval tmpCFNDir := $(shell mktemp -d))
	$(eval tmpCFNDir := .tmp)

	$(eval assetBucket := sam-${awsAccount}-${awsRegion})
	if aws s3api head-bucket --bucket ${assetBucket} 2>/dev/null; \
		then echo Bucket ${assetBucket} exists; \
		else echo Creating bucket ${assetBucket} && \
			aws s3 mb s3://${assetBucket} --region ${awsRegion} ; \
		fi

	if test -e ${tmpCFNDir}; \
		then echo ${tmpCFNDir} folder exists; \
		else echo Creating ${tmpCFNDir} folder && \
			mkdir ${tmpCFNDir};
		fi

	sam package -t samples/sam-template.yaml --output-template-file ${tmpCFNDir}/cfn1-template.tmp.yaml --s3-bucket ${assetBucket}

	rm -rf samples/assets

.PHONY : test-cfn
test-cfn : package-template
	sam-cfn-publish \
		--working-folder ${tmpCFNDir} \
    	--cfn-input-template ${tmpCFNDir}/cfn1-template.tmp.yaml \
    	--cfn-output-template samples/cfn-template.yaml \
    	--target-asset-folder samples/assets/cfn \
		--target-asset-bucket AssetBucket \
		--move-assets \
		--verbose

	# rm -rf ${tmpCFNDir}

.PHONY : deploy-cfn
deploy-cfn : test-cfn
	$(eval awsAccount := $(shell aws sts get-caller-identity --query Account --output text))

	$(eval assetBucket := cfn-${awsAccount}-${awsRegion})
	if aws s3api head-bucket --bucket ${assetBucket} 2>/dev/null; \
		then echo Bucket ${assetBucket} exists; \
		else echo Creating bucket ${assetBucket} && \
			aws s3 mb s3://${assetBucket} --region ${awsRegion} ; \
		fi

	aws s3 sync samples/assets/cfn s3://${assetBucket} --delete

	aws cloudformation deploy --stack-name sam-cfn-publish-sample --template-file samples/cfn-template.yaml \
	 	--parameter-overrides AssetBucket=${assetBucket} \
		--capabilities CAPABILITY_IAM CAPABILITY_AUTO_EXPAND

.PHONY : test-sam
test-sam : package-template

	@echo Working folder ${tmpCFNDir}

	sam-cfn-publish \
		--working-folder ${tmpCFNDir} \
		--input-format SAM \
        --output-format SAM \
    	--cfn-input-template ${tmpCFNDir}/cfn1-template.tmp.yaml \
    	--cfn-output-template samples/cfn-template.yaml \
    	--target-asset-folder samples/assets/cfn \
		--target-asset-bucket AssetBucket \
		--move-assets \
		--verbose

	# rm -rf ${tmpCFNDir}

.PHONY : deploy-sam
# deploy-sam : test-sam
deploy-sam :
	$(eval awsAccount := $(shell aws sts get-caller-identity --query Account --output text))

	$(eval assetBucket := cfn-${awsAccount}-${awsRegion})
	if aws s3api head-bucket --bucket ${assetBucket} 2>/dev/null; \
		then echo Bucket ${assetBucket} exists; \
		else echo Creating bucket ${assetBucket} && \
			aws s3 mb s3://${assetBucket} --region ${awsRegion} ; \
		fi

	aws s3 sync samples/assets/cfn s3://${assetBucket} --delete

	sam deploy --stack-name sam-sam-publish-sample --template-file samples/cfn-template.yaml \
	 	--parameter-overrides AssetBucket=${assetBucket} \
		--capabilities CAPABILITY_IAM CAPABILITY_AUTO_EXPAND