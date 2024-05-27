import json
import unittest.mock

import pytest

from pantos.servicenode.restapi import BidInteractor
from pantos.servicenode.restapi import _BidsSchema


def test_bids_correct(bids, test_client):
    with unittest.mock.patch.object(BidInteractor,
                                    'get_cross_blockchain_bids',
                                    return_value=bids):
        response = test_client.get(
            '/bids?source_blockchain=1&destination_blockchain=3')

    assert response.status_code == 200
    assert json.loads(response.text) == bids


@pytest.mark.parametrize(
    'query_param,expected_code,expected_response',
    [('source_blockchain=1&destination_blockchain=2', 400, {
        'destination_blockchain': ['Must be one of: 0, 1, 3, 4, 5, 6, 7, 8.']
    }),
     ('source_blockchain=2&destination_blockchain=3', 400, {
         'source_blockchain': ['Must be one of: 0, 1, 3, 4, 5, 6, 7, 8.']
     }),
     ('', 400, {
         'destination_blockchain': ['Missing data for required field.'],
         'source_blockchain': ['Missing data for required field.']
     }),
     ('source_blockchain_1', 400, {
         'destination_blockchain': ['Missing data for required field.'],
         'source_blockchain': ['Missing data for required field.'],
         'source_blockchain_1': ['Unknown field.']
     }),
     ('destination_blockchain=1', 400, {
         'source_blockchain': ['Missing data for required field.']
     }),
     ('source_blockchain=abc&destination_blockchain=3', 400, {
         'source_blockchain': ['Not a valid integer.']
     }),
     ('source_blockchain=1&destination_blockchain=abc', 400, {
         'destination_blockchain': ['Not a valid integer.']
     }),
     ('destination_blockchain=3', 400, {
         'source_blockchain': ['Missing data for required field.']
     }),
     ('source_blockchain=3', 400, {
         'destination_blockchain': ['Missing data for required field.']
     }),
     ('test=3&abc=5', 400, {
         'abc': ['Unknown field.'],
         'destination_blockchain': ['Missing data for required field.'],
         'source_blockchain': ['Missing data for required field.'],
         'test': ['Unknown field.']
     })])
def test_bids_incorrect_blockchain_id(query_param, expected_code,
                                      expected_response, test_client):
    response = test_client.get(f"/bids?{query_param}")

    assert response.status_code == expected_code
    assert json.loads(response.text)['message'] == expected_response


@unittest.mock.patch('pantos.servicenode.restapi.internal_server_error')
@unittest.mock.patch.object(_BidsSchema, 'load', side_effect=Exception)
def test_transfer_exception(mocked_load, mocked_internal_server_error,
                            test_client):
    response = test_client.get(
        '/bids?source_blockchain=1&destination_blockchain=3')

    mocked_internal_server_error.assert_called_once_with()
    assert response.status_code == 500
