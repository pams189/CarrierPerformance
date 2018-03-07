from services import settings
from services import root_dir
from pymongo import MongoClient
import pandas as pd
import math
from sklearn import linear_model
from sklearn.svm import SVR

def create_json_object_from_dict(in_dict):
    load = {}
    rankings_json = []
    carrier = {'LaneName': None, 'Violations': None, 'Mean':None, 'Count': None,'Performance Rating':None}

    for key, value in in_dict.items():
        load['CARRIER'] = key
        rankings_json.append(load)
        carrier['LaneName'] = str(value[settings.lane])
        carrier['Violations'] = str(value[settings.mismatch])
        carrier['Mean'] = str(math.ceil(value[settings.mean]))
        carrier['Count'] = str(value[settings.count])
        carrier['Performance Rating'] = str(value[settings.percentage])
        rankings_json.append(carrier)
        carrier = {}
        load = {}
    return rankings_json

def get_sorted_dict_from_data(loads):

    load_keys = dict()
    keys = loads.groups.keys()
    TIME_VALIDATE = False

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
        tmp_list.append(round(((total_cnt - after_mismatch_eta) / total_cnt) * 100))
        tmp_list.append(total_cnt)
        load_keys[i] = tmp_list
        tmp_list = []

    load_keys = get_loads_after_predicted_values_from_svr_regression(load_keys,TIME_VALIDATE)

    if TIME_VALIDATE:
        sum_mean = 0
        for value in load_keys.values():
            sum_mean = sum_mean + value[settings.mean]

        for key, val in load_keys.items():
            val[settings.percentage] = round((1- (val[settings.mean]/sum_mean))*100)
            load_keys[key] = val


    sorted_loads = dict(sorted(load_keys.items(), key=lambda x: (x[1][3]), reverse=True))

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
    load_keys[settings.CARRIERID] = tmp_list

    sorted_loads = dict(sorted(load_keys.items(), key=lambda x: (x[1][3]), reverse=True))

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
def get_loads_after_predicted_values_from_svr_regression(predicted_loads,TIME_VALIDATE):

    svr_regression_data = pd.DataFrame.from_dict(predicted_loads, orient='index')
    svr_regression_data.columns = ['mismatch', 'lane', 'mean', 'percentage', 'count']
    target = pd.DataFrame(svr_regression_data.mismatch, columns=["mismatch"])

    if not TIME_VALIDATE:
        X = svr_regression_data[['count']]
    else:
        X = svr_regression_data[['count','mean']]
        
    y = target["mismatch"]

    #lm = svr_model.svrRegression()
    clf = SVR(kernel='rbf', C=1e3, gamma=0.1)
    model = clf.fit(X, y)
    predictions = clf.predict(X)
    predict_values = []
    for i in predictions:
        predict_values.append(round(i))

    keys = list(predicted_loads.keys())
    count = 0

    for val, pred in zip(predicted_loads.values(), predict_values):
        val[settings.mismatch] = pred
        val[settings.percentage] = round(((val[settings.count] - val[settings.mismatch]) / val[settings.count]) * 100)
        predicted_loads[keys[count]] = val
        count = count + 1

    return predicted_loads