import pandas as pd
from services import settings
from services import root_dir

root_dir = root_dir()
file_name = "/database/"+settings.CSVFILE
csv_file = root_dir+file_name
json_file = root_dir+"/database/"+settings.JSONFILE

print(csv_file,json_file)

with open(csv_file, "r") as f:
    csvfile = pd.read_csv(f)
csvfile.to_json(json_file)
df = pd.read_json(json_file)
print(df.head)
