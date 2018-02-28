import pytest
from services import CarrierAPI
import json

@pytest.fixture
def client(request):
    app = CarrierAPI.CarrierApp
    test_client = app.test_client()
    def teardown():
        pass
    request.addfinalizer(teardown)
    return test_client

def test_get_response_eta_for_all_loads(client):

    response = client.get('/CarrierAPI/Rating/carrier/eta')
    assert response.status_code == 200

def test_get_response_eta_for_specific_load(client):

    response = client.get('/CarrierAPI/Rating/carrier/L1/eta')
    assert response.status_code == 200

def test_get_response_eta_for_nonexist_load(client):

    response = client.get('/CarrierAPI/Rating/carrier/L5/eta')
    assert response.status_code == 404

def test_get_response_eta_for_nonexist_load_1(client):

    response = client.get('/CarrierAPI/Rating/carrier/L6/eta')
    assert response.status_code == 404

def test_get_response_eta_for_invalid_input(client):

    response = client.get('/CarrierAPI/Rating/carrier/fallout')
    assert response.status_code == 404

def test_get_response_eta_for_invalid_input_1(client):

    response = client.get('/CarrierAPI/Rating/carrier/accept')
    assert response.status_code == 404

def test_get_eta_for_all_loads(client):

    response = client.get('/CarrierAPI/Rating/carrier/eta')
    assert response.status_code == 200
    json_data = json.loads(response.data)
    assert_valid_schema(json_data)


def test_get_eta_for_specific_load(client):

    response = client.get('/CarrierAPI/Rating/carrier/L1/eta')
    assert response.status_code == 200
    json_data = json.loads(response.data)
    assert_valid_schema(json_data)

def test_get_eta_for_specific_load_1(client):

    response = client.get('/CarrierAPI/Rating/carrier/L2/eta')
    assert response.status_code == 200
    json_data = json.loads(response.data)
    assert_valid_schema(json_data)

def test_get_eta_for_specific_load_2(client):

    response = client.get('/CarrierAPI/Rating/carrier/L3/eta')
    assert response.status_code == 200
    json_data = json.loads(response.data)
    assert_valid_schema(json_data)

def test_get_eta_for_specific_load_3(client):

    response = client.get('/CarrierAPI/Rating/carrier/L4/eta')
    assert response.status_code == 200
    json_data = json.loads(response.data)
    assert_valid_schema(json_data)

def assert_valid_schema(data):
    for key, value in data.items():
        assert ('CarrierRatingRanking' in key)
        assert ('LOAD' in value[0])
        assert ('Violations' in value[1])
        assert ('CarrierName' in value[1])
        #assert ('Difference in ETA' in value[1])
        assert ('Performance Rating' in value[1])
