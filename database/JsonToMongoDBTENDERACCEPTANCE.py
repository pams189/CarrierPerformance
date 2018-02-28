from pymongo import MongoClient
from services import settings
from services import GeneralFunctions
import csv

client = MongoClient()
db = client['CarrierRatingTable']


reader = csv.DictReader(open(GeneralFunctions.get_csv_file()))
count = 1
tmp_dict = {}
tmp_dict_1 = {}

for row in reader:
    tmp_dict = {"_id": count}
    tmp_dict_1 = row
    tmp_dict.update(tmp_dict_1)
    doc_id = db.CarrierRatingTableTENDERACCEPTANCE.insert(tmp_dict)
    count = count + 1

records = db.CarrierRatingTableTENDERACCEPTANCE.find()
for i in records:
    print(i)