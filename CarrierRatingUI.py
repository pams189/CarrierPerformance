from flask import Flask,render_template,request,redirect,url_for
import os
import settings
import pandas as pd
import requests
import json
import matplotlib.pyplot as plt
import io
import urllib.parse
import base64
import xmltodict
from pymongo import MongoClient
import re

app = Flask(__name__,static_url_path='/static')
app.jinja_env.filters['zip'] = zip

@app.route('/')
def login():
    return redirect(url_for('show_lanes'))

@app.route('/lanes', methods=['GET', 'POST'])
def show_lanes():
    rootdir = os.path.dirname(os.path.realpath(__file__))
    csv_file = rootdir + "/CSVFILES/" + settings.CSVFILE
    data = pd.read_csv(csv_file)
    lane_data = list(set(data['Plan_Lane']))

    return render_template('lanes.html', lane_data=lane_data)

@app.route('/rating_options/<lane_id>', methods=['GET', 'POST'])
def carrier_rating_options(lane_id):
    results = {}
    errors = []
    plot_data = ""
    titles = ""
    rating_carrier= ""
    rating_carrier_found = False
    ETA_CONSIDER = False
    if request.method == "GET":
        return render_template('options.html')
    if request.method == "POST":
        show_data_option = request.form.get("data")
        if str(show_data_option) == "PLANDATA":
            return redirect(url_for('show_planned_data',lane_id=lane_id, msg="Planning Data"))

        #selected_rating_option = request.form.getlist("rating")

        options = 'ETA,FALLOUTS,TENDERACCEPTANCE,SERVICELEVELS'
        try:
            data = requests.get('http://127.0.0.1:5000/CarrierAPI/Rating/carrier/'+str(lane_id)+'/'+options)
        except:
            errors.append(
                "Unable to get URL. Please make sure it's valid and try again."
            )
            return render_template('options.html', errors=errors, results=results)

        if data.status_code != 200:
            errors.append(
                "Unable to get URL. Please make sure it's valid and try again."
            )
            return render_template('options.html', errors=errors, results=results)

        api_data = json.loads(data.text)
        val_list = []
        load_value = None
        plot_data = []
        titles = []
        for key, values in api_data.items():
            for opt_key,opt_value in values.items():
                results = {}
                for list_val in opt_value:
                    for load_key,load_val in list_val.items():
                        if load_key == 'CARRIER':
                            if not rating_carrier_found and opt_key == 'OVERALL':
                                rating_carrier = load_val
                                rating_carrier_found = True
                            load_value = load_val
                        else:
                            val_list.append(load_val)
                    results[load_value] = val_list
                    val_list = []

                data = pd.DataFrame.from_dict(results, orient='index')
                data.columns = ['Lane', 'Load Violations', 'Mean','Loads Assigned','Percentage']
                data['Load Violations'] = pd.to_numeric(data['Load Violations'])
                data['Loads Assigned'] = pd.to_numeric(data['Loads Assigned'])
                data['Percentage'] = pd.to_numeric(data['Percentage'])

                if opt_key == "FALLOUTS":
                    opt_key = "Fallouts"
                elif opt_key == "TENDERACCEPTANCE":
                    opt_key = "Tender Acceptance"
                elif opt_key == "SERVICELEVELS":
                    opt_key = "Service Levels"
                elif opt_key == "OVERALL":
                    opt_key = "Overall"

                if opt_key == "ETA":
                    data[['Load Violations', 'Loads Assigned']].plot(kind='bar', title="On Time Pickup/Delivery Violations", legend=True, fontsize=12)
                else:
                    data[['Load Violations', 'Loads Assigned']].plot(kind='bar',
                                                                     title=opt_key + " Violations",
                                                                     legend=True, fontsize=12)
                img = io.BytesIO()
                plt.savefig(img, format='png')
                img.seek(0)
                plot_data.append(urllib.parse.quote(base64.b64encode(img.read()).decode()))
                if opt_key == "ETA":
                    titles.append("On Time Pickup/Delivery Violations")
                else:
                    titles.append(opt_key + " Violations")
                data['Mean'] = pd.to_numeric(data['Mean'])
                if opt_key == "ETA":
                    ETA_CONSIDER = True
                    data[['Mean']].plot(kind='bar', title="Average Time Violations(In Secs)", legend=True, fontsize=12)
                    img1 = io.BytesIO()
                    plt.savefig(img1, format='png')
                    img1.seek(0)
                    plot_data.append(urllib.parse.quote(base64.b64encode(img1.read()).decode()))
                    titles.append("Average Time Violations(In Secs)")
                else:
                    ETA_CONSIDER = False

                if opt_key == "ETA":
                    data[['Percentage']].plot(kind='bar', title="Carrier Performance Rating Based On Time Pickup/Delivery", legend=True, fontsize=12)
                elif opt_key == "Overall":
                    data[['Percentage']].plot(kind='bar',
                                              title="Overall Carrier Performance Rating",
                                              legend=True, fontsize=12)
                else:
                    data[['Percentage']].plot(kind='bar',
                                              title="Carrier Performance Rating Based On " + opt_key,
                                              legend=True, fontsize=12)
                img2 = io.BytesIO()
                plt.savefig(img2, format='png')
                img2.seek(0)
                plot_data.append(urllib.parse.quote(base64.b64encode(img2.read()).decode()))
                if opt_key == "ETA":
                    titles.append("Carrier Performance Rating Based On Time Pickup/Delivery")
                elif opt_key == "Overall":
                    titles.append("Overall Carrier Performance Rating")
                else:
                    titles.append("Carrier Performance Rating Based On "+opt_key)

        if not ETA_CONSIDER:
            for key,values in results.items():
                del values[2]
        return render_template('options.html',errors=errors, results=results, plot_url=plot_data, titles=titles, ETA_CONSIDER=ETA_CONSIDER, lane_id=lane_id, rating_carrier=rating_carrier)

@app.route('/show_planned_data/<lane_id>/<msg>', methods=['GET', 'POST'])
def show_planned_data(lane_id,msg):
    client = MongoClient()
    db = client['CarrierRatingTable']
    records = db.CarrierRatingTableLoads.find()
    data = pd.DataFrame.from_records(records)
    data = data.dropna()
    settings.LANEID = lane_id
    '''rootdir = os.path.dirname(os.path.realpath(__file__))
    csv_file = rootdir + "/CSVFILES/" + settings.CSVFILE
    data = pd.read_csv(csv_file)'''
    data = data[data[settings.LANE] == settings.LANEID]
    carriers = list(set(data[settings.CARRIER]))
    show_data = data[['Plan_Lane','Plan_Load','Plan_Carrier','Cost']]

    return render_template('plan_data.html', lane_id=lane_id, data=show_data,carriers=carriers,msg=msg)

@app.route('/show_rate_changes_after_carrier/<load_id>/<carrier_id>/<lane_id>/<cost>', methods=['GET', 'POST'])
def show_rate_changes_after_carrier(load_id,carrier_id,lane_id,cost):
    carrier_option = request.form.get("carrier")
    '''rootdir = os.path.dirname(os.path.realpath(__file__))
    bat_file = rootdir + "/plr/" + settings.BATFILE
    os.system(bat_file)
    out_file = rootdir + "/plr/" + settings.OUTFILE
    with open(out_file) as fd:
        result = xmltodict.parse(fd.read())'''
    new_cost = int(cost)+35
    return render_template('displaychanges.html',load_id=load_id,old_carrier_id=carrier_id,new_carrier_id=carrier_option,lane_id=lane_id,old_cost=cost,new_cost=new_cost)

@app.route('/commit_changes/<load_id>/<old_carrier_id>/<lane_id>/<new_carrier_id>/<cost>',methods=['GET', 'POST'])
def commit_changes(load_id,old_carrier_id,lane_id,new_carrier_id,cost):
    client = MongoClient()
    db = client['CarrierRatingTable']
    record = db.CarrierRatingTableLoads.find({'Plan_Lane': lane_id, 'Plan_Load': load_id, 'Plan_Carrier': old_carrier_id})
    if record:
        db.CarrierRatingTableLoads.update({'Plan_Lane': lane_id, 'Plan_Load': load_id, 'Plan_Carrier': old_carrier_id}, {'$set':{'Plan_Carrier': new_carrier_id, 'Cost': cost}})
    return redirect(url_for('show_planned_data',lane_id=lane_id, msg="Planning Data"))

@app.route('/carrier_change',methods=['GET', 'POST'])
def carrier_change():
    values = request.form.get('carrieroption')
    values = re.sub(r'[()]', '', values)
    values = values.split(',')
    load_data = []
    for val in values:
        val = re.sub(r'\'', '', val)
        load_data.append(val.strip())
    client = MongoClient()
    db = client['CarrierRatingTable']
    records = db.CarrierRatingTableETA.find()
    data = pd.DataFrame.from_records(records)
    data = data.dropna()

    load_data = list(load_data)
    settings.LANEID = load_data[0]
    data = data[data[settings.LANE] == settings.LANEID]
    carriers = list(set(data[settings.CARRIER]))

    return render_template('carrier_change.html', values=load_data,carriers=carriers)

@app.route('/update_planned_data/<lane_id>/<carrier_id>', methods=['GET', 'POST'])
def update_planned_data(lane_id,carrier_id):
    client = MongoClient()
    db = client['CarrierRatingTable']
    records = db.CarrierRatingTableLoads.find()
    data = pd.DataFrame.from_records(records)
    data = data.dropna()
    settings.LANEID = lane_id
    data = data[data[settings.LANE] == settings.LANEID]
    cost_list = list(data['Cost'])
    show_data = data[['Plan_Lane', 'Plan_Load', 'Plan_Carrier', 'Cost']]

    count = 20
    cost_index = 0
    records = db.CarrierRatingTableLoads.find()
    for i in records:
        if i['Plan_Carrier'] == carrier_id:
            cost_index = cost_index + 1
            count = 10
            continue
        db.CarrierRatingTableLoads.update(
            {'Plan_Lane': lane_id, 'Plan_Carrier': {'$ne': carrier_id }},
            {'$set': {'Plan_Carrier': carrier_id, 'Cost': str(count+int(cost_list[cost_index]))}})
        count = count+10
        cost_index = cost_index+1

    new_records = db.CarrierRatingTableLoads.find()
    new_data = pd.DataFrame.from_records(new_records)
    new_data = new_data.dropna()
    new_data = new_data[new_data[settings.LANE] == settings.LANEID]
    new_data = new_data[['Plan_Carrier', 'Cost']]
    final_data = pd.concat([show_data,new_data], axis=1)
    final_data.columns = ['lane', 'load', 'old_carrier', 'old_cost', 'new_carrier','new_cost']
    return render_template('new_plan_data.html', lane_id=lane_id, data=final_data)

if __name__ == '__main__':
    app.run(port=8080)
