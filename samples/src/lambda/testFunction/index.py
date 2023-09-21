import json

def lambda_handler(event, context):
    print('REQUEST RECEIVED:\n' + json.dumps(event))

    return {"statusCode": 200,
            "body": "SAM Rocks!"}

