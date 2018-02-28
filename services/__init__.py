import os
from flask import Flask,Blueprint
from flask_restplus import Api

def root_dir():
    return os.path.dirname(os.path.realpath(__file__ + '/..'))

def App():
    app = Flask(__name__)
    blueprint = Blueprint('CarrierAPI', __name__, url_prefix='/CarrierAPI')
    api = Api(blueprint, version='1.0', title='CarrierRating API', description='Carrier Rating Ranking API', doc='/doc')

    app.register_blueprint(blueprint)
    app.config['SWAGGER_UI_JSONEDITOR'] = True
    return api,app