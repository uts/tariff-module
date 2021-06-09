from tariff_model.aws_handler import s3_to_json

bucket = 'tariff-model-test-data'

ikea_tariff_dict = s3_to_json(bucket, 'ikea_tariff.json')
print(ikea_tariff_dict)