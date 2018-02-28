from flask_restplus import Resource,abort
import pandas as pd
from services import App
from services import settings
from services import GeneralFunctions
from pymongo import MongoClient
import math

carrierAPI,CarrierApp = App()
ns = carrierAPI.namespace('Rating', description='Carrier Rating')

client = MongoClient()
db = client['CarrierRatingTable']

@ns.route('/carrier/<lane_id>/<input>')
class CarrierRatingByLaneID(Resource):

    def get(self,lane_id,input):
        carrierrating = {}
        input = input.split(',')
        overall_rating = {}
        count = 0
        for each_input in input:
            if each_input:
                count = count+1
                plan_val = settings.PLANNING + each_input.upper()
                exec_val = settings.EXECUTION + each_input.upper()
                settings.PLANINPUTVALUE = plan_val
                settings.EXECINPUTVALUE = exec_val
                settings.INPUT = each_input
                collection_input = each_input.upper()
                settings.LANEID = lane_id.upper()

                records = GeneralFunctions.get_mongodb_collection(collection_input)
                if records == None:
                    abort(404)

                data = pd.DataFrame.from_records(records)
                data = data.drop('_id', 1)

                if {plan_val, exec_val}.issubset(data.columns):
                    pass
                else:
                    abort(404)

                if data[plan_val].dtype == object:
                    if "AM" in data.iloc[0][plan_val] or "PM" in data.iloc[0][plan_val]:
                        data[settings.DIFF] = (pd.to_datetime(data[exec_val]) - pd.to_datetime(data[plan_val])).dt.total_seconds()
                    elif data[plan_val].dtype == 'int64':
                        data[settings.DIFF] = pd.to_numeric(data[exec_val]) - pd.to_numeric(data[plan_val])
                else:
                    if data[plan_val].dtype == 'int64':
                        data[settings.DIFF] = data[exec_val] - data[plan_val]

                if settings.LANE in data.columns:
                    data = data[data[settings.LANE]==settings.LANEID]
                else:
                    abort(404)

                if settings.CARRIER in data.columns:
                    data_srt = data.sort_values(by=settings.CARRIER)
                    loads = data_srt.groupby(settings.CARRIER)
                else:
                    abort(404)

                sorted_loads = GeneralFunctions.get_sorted_dict_from_data(loads)
                if overall_rating:
                    for key,val in overall_rating.items():
                        for re_key,re_val in sorted_loads.items():
                            if key == re_key:
                                val[0] = val[0]+re_val[0]
                                val[3] = val[3]+re_val[3]
                                val[4] = val[4]+re_val[4]
                                overall_rating[key] = val
                else:
                    overall_rating = sorted_loads
                rankings = GeneralFunctions.create_json_object_from_dict(sorted_loads)
                carrierrating[each_input.upper()] = rankings

        if count > 1:
            for over_key,over_val in overall_rating.items():
                over_val[3] = math.ceil(over_val[3]/count)
                overall_rating[over_key] = over_val

            sorted_loads = dict(sorted(overall_rating.items(), key=lambda x: (x[1][3]), reverse=True))
            rankings = GeneralFunctions.create_json_object_from_dict(sorted_loads)
            carrierrating['OVERALL'] = rankings

        return {'CarrierRatingRanking': carrierrating}

@ns.route('/carrier/<lane_id>/<carrier_id>/<input>')
class CarrierRatingByCarrierID(Resource):

    def get(self,lane_id,carrier_id,input):
        plan_val = settings.PLANNING + input.upper()
        exec_val = settings.EXECUTION + input.upper()
        settings.PLANINPUTVALUE = plan_val
        settings.EXECINPUTVALUE = exec_val
        settings.INPUT = input
        settings.CARRIERID = str(carrier_id).upper()
        collection_input = input.upper()
        settings.LANEID = lane_id.upper()

        records = GeneralFunctions.get_mongodb_collection(collection_input)
        if records == None:
            abort(404)

        data = pd.DataFrame.from_records(records)
        data = data.drop('_id', 1)

        if {plan_val, exec_val}.issubset(data.columns):
            pass
        else:
            abort(404)

        if data[plan_val].dtype == object:
            if "AM" in data.iloc[0][plan_val] or "PM" in data.iloc[0][plan_val]:
                data[settings.DIFF] = (pd.to_datetime(data[exec_val]) - pd.to_datetime(data[plan_val])).dt.total_seconds()
            else:
                data[settings.DIFF] = pd.to_numeric(data[exec_val]) - pd.to_numeric(data[plan_val])
        else:
            data[settings.DIFF] = data[exec_val] - data[plan_val]

        if settings.LANE in data.columns:
            data = data[data[settings.LANE]==settings.LANEID]
        else:
            abort(404)

        if settings.CARRIER in data.columns:
            specific_carrier = data[data[settings.CARRIER]==settings.CARRIERID]
        else:
            abort(404)

        if(len(specific_carrier) == 0):
            abort(404)

        sorted_loads = GeneralFunctions.get_sorted_dict_from_specific_carrier_data(specific_carrier)
        rankings = GeneralFunctions.create_json_object_from_dict(sorted_loads)

        return {'CarrierRatingRanking': rankings}

if __name__ == '__main__':
    CarrierApp.run(debug=True)
