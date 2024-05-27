import json
import unittest.mock
import uuid

import flask_restful  # type: ignore
import marshmallow

from pantos.servicenode.business.transfers import \
    TransferInteractorResourceNotFoundError
from pantos.servicenode.restapi import TransferInteractor
from pantos.servicenode.restapi import _TransferStatusSchema


@unittest.mock.patch('pantos.servicenode.restapi.ok_response',
                     lambda data: data)
@unittest.mock.patch.object(TransferInteractor, 'find_transfer')
@unittest.mock.patch.object(_TransferStatusSchema, 'load')
def test_transfer_status_correct(mocked_load, mocked_find_transfer,
                                 test_client, uuid_, source_blockchain,
                                 destination_blockchain, sender_address,
                                 recipient_address, source_token_address,
                                 destination_token_address, amount, fee,
                                 status, transfer_id, transaction_id,
                                 find_transfer_response):
    expected_transfer_status = {
        'task_id': uuid_,
        'source_blockchain_id': source_blockchain.value,
        'destination_blockchain_id': destination_blockchain.value,
        'sender_address': sender_address,
        'recipient_address': recipient_address,
        'source_token_address': source_token_address,
        'destination_token_address': destination_token_address,
        'amount': amount,
        'fee': fee,
        'status': status.name.lower(),
        'transfer_id': transfer_id,
        'transaction_id': transaction_id
    }
    mocked_load.return_value = uuid.UUID(uuid_)
    mocked_find_transfer.return_value = find_transfer_response

    response = test_client.get(f'/transfer/{uuid_}/status')

    assert response.status_code == 200
    assert json.loads(response.text) == expected_transfer_status


@unittest.mock.patch(
    'pantos.servicenode.restapi.resource_not_found',
    lambda error_message: flask_restful.abort(404, message=error_message))
@unittest.mock.patch.object(_TransferStatusSchema,
                            'load',
                            side_effect=marshmallow.ValidationError(''))
def test_transfer_status_validation_error(mocked_load, test_client, uuid_):
    expected_error_messsage = f'task ID {uuid_} is not a UUID'

    response = test_client.get(f'/transfer/{uuid_}/status')

    assert response.status_code == 404
    assert json.loads(response.text)['message'] == expected_error_messsage


@unittest.mock.patch(
    'pantos.servicenode.restapi.resource_not_found',
    lambda error_message: flask_restful.abort(404, message=error_message))
@unittest.mock.patch.object(TransferInteractor, 'find_transfer')
@unittest.mock.patch.object(_TransferStatusSchema, 'load')
def test_transfer_status_resource_not_found_error(mocked_load,
                                                  mocked_find_transfer,
                                                  test_client, uuid_):
    mocked_find_transfer.side_effect = \
        TransferInteractorResourceNotFoundError('')
    expected_error_messsage = f'task ID {uuid_} is unknown'
    response = test_client.get(f'/transfer/{uuid_}/status')

    assert response.status_code == 404
    assert json.loads(response.text)['message'] == expected_error_messsage


@unittest.mock.patch('pantos.servicenode.restapi.internal_server_error',
                     lambda error_message: flask_restful.abort(500))
@unittest.mock.patch.object(_TransferStatusSchema,
                            'load',
                            side_effect=Exception)
def test_transfer_status_internal_error(mocked_load, test_client, uuid_):
    response = test_client.get(f'/transfer/{uuid_}/status')

    assert response.status_code == 500
