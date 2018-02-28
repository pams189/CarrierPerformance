from services import settings
from services import root_dir
from pymongo import MongoClient
import pandas as pd
import math

def create_json_object_from_dict(in_dict):
    load = {}
    rankings_json = []
    #carrier = {'Violations': None, 'CarrierName': None, 'Difference in ' + settings.INPUT.upper(): None, 'Percentage': None}
    carrier = {'LaneName': None, 'Violations': None, 'Mean':None, 'Count': None,'Performance Rating':None}

    for key, value in in_dict.items():
        load['CARRIER'] = key
        rankings_json.append(load)
        carrier['LaneName'] = str(value[1])
        carrier['Violations'] = str(value[0])
        carrier['Mean'] = str(math.ceil(value[2]))
        #carrier['Difference in ' + settings.INPUT.upper()] = str(value[2])
        carrier['Count'] = str(value[4])
        carrier['Performance Rating'] = str(value[3])
        rankings_json.append(carrier)
        carrier = {}
        load = {}
    return rankings_json

def get_sorted_dict_from_data(loads):

    load_keys = dict()
    keys = loads.groups.keys()
    TIME_VALIDATE = False
    '''for name, g in loads:
        sf = name
        load_keys.setdefault(sf, [])'''
    tmp_list = []
    for i in keys:
        lf = loads.get_group(i)
        if "AM" in lf.iloc[0][settings.PLANINPUTVALUE] or "PM" in lf.iloc[0][settings.PLANINPUTVALUE]:
            TIME_VALIDATE = True
        total_cnt = len(lf)
        lf_1 = lf[lf[settings.PLANINPUTVALUE] != lf[settings.EXECINPUTVALUE]]
        after_mismatch_eta = len(lf_1[lf_1 == True])
        tmp_list.append(after_mismatch_eta)
        tmp_list.append(lf.iloc[0][settings.LANE])
        if settings.DIFF in lf_1.columns:
            mean_value = lf_1[settings.DIFF].mean()
        else:
            mean_value = after_mismatch_eta
        tmp_list.append(mean_value)
        tmp_list.append(math.ceil(((total_cnt - after_mismatch_eta) / total_cnt) * 100))
        tmp_list.append(total_cnt)
        load_keys[i] = tmp_list
        tmp_list = []

    if TIME_VALIDATE:
        sum_mean = 0
        for value in load_keys.values():
            sum_mean = sum_mean + value[2]

        for key, val in load_keys.items():
            val[3] = math.ceil((1- (val[2]/sum_mean))*100)
            load_keys[key] = val

    sorted_loads = dict(sorted(load_keys.items(), key=lambda x: (x[1][3]), reverse=True))
    '''print(load_keys)
    for key, value in load_keys.items():
        sorted_loads[key] = sorted(value, key=lambda x: (x[0], x[2]))'''

    return sorted_loads

def get_sorted_dict_from_specific_carrier_data(specific_carrier):

    load_keys = dict()
    tmp_list = []
    total_cnt = len(specific_carrier)
    lf_1 = specific_carrier[specific_carrier[settings.PLANINPUTVALUE] != specific_carrier[settings.EXECINPUTVALUE]]
    after_mismatch_eta = len(lf_1[lf_1 == True])
    tmp_list.append(after_mismatch_eta)
    tmp_list.append(specific_carrier.iloc[0][settings.LANE])
    if settings.DIFF in lf_1.columns:
        mean_value = lf_1[settings.DIFF].mean()
    else:
        mean_value = after_mismatch_eta
    tmp_list.append(mean_value)
    tmp_list.append(100)
    tmp_list.append(total_cnt)
    #load_keys.setdefault(settings.LOADID, []).append(tmp_list)
    load_keys[settings.CARRIERID] = tmp_list

    sorted_loads = dict(sorted(load_keys.items(), key=lambda x: (x[1][3]), reverse=True))
    '''for key, value in load_keys.items():
        sorted_loads[key] = sorted(value, key=lambda x: (x[0], x[2]), reverse=True)'''

    return sorted_loads

def get_json_file():
    parent_root_dir = root_dir()
    json_file = parent_root_dir + "/database/" + settings.JSONFILE
    return json_file

def get_csv_file():
    parent_root_dir = root_dir()
    csv_file = parent_root_dir + "/database/" + settings.CSVFILE
    return csv_file

def get_mongodb_collection(input):
    client = MongoClient()
    db = client['CarrierRatingTable']
    for i in db.list_collection_names():
        if input in i:
            str = db[i]
            records = str.find()
            return records
    else:
        return None