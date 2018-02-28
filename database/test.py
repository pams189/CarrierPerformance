from pymongo import MongoClient
import csv

reader = csv.DictReader(open("ETA_CSV.csv"))
for row in reader:
    print(dict(row))

