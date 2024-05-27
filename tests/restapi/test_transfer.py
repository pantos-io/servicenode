import json
import unittest.mock

import flask_restful  # type: ignore
import marshmallow
from pantos.common.blockchains.enums import Blockchain

from pantos.servicenode.business.transfers import SenderNonceNotUniqueError
from pantos.servicenode.business.transfers import \
    TransferInteractorBidNotAcceptedError
from pantos.servicenode.restapi import TransferInteractor
from pantos.servicenode.restapi import _TransferSchema


@unittest.mock.patch('pantos.servicenode.restapi.ok_response',
                     lambda data: data)
@unittest.mock.patch.object(_TransferSchema, 'load')
def test_transfer_correct(mocked_load, test_client, uuid_,
                          initiate_transfer_request):
    mocked_load.return_value = initiate_transfer_request
    with unittest.mock.patch.object(TransferInteractor, 'initiate_transfer',
                                    return_value=uuid_):
        response = test_client.post('/transfer', json={})

    assert response.status_code == 200
    assert json.loads(response.text)['task_id'] == str(uuid_)


@unittest.mock.patch('pantos.servicenode.restapi.not_acceptable')
@unittest.mock.patch.object(_TransferSchema, 'load',
                            side_effect=marshmallow.ValidationError(''))
def test_transfer_validation_error(mocked_load, mocked_not_acceptable,
                                   test_client):
    mocked_not_acceptable.side_effect = \
        lambda error_message: flask_restful.abort(  # noqa: E731
            406, message=error_message)

    response = test_client.post('/transfer', json={})

    mocked_not_acceptable.assert_called_once_with([''])
    assert response.status_code == 406


@unittest.mock.patch('pantos.servicenode.restapi.conflict')
@unittest.mock.patch.object(
    TransferInteractor, 'initiate_transfer',
    side_effect=SenderNonceNotUniqueError(Blockchain.ETHEREUM, '', 0))
@unittest.mock.patch.object(_TransferSchema, 'load')
def test_transfer_sender_nonce_not_unique_error(mocked_load,
                                                mocked_initiate_transfer,
                                                mocked_conflict, test_client,
                                                initiate_transfer_request):
    mocked_load.return_value = initiate_transfer_request
    mocked_conflict.side_effect = \
        lambda error_message: flask_restful.abort(  # noqa: E731
            406, message=error_message)

    response = test_client.post('/transfer', json={})

    mocked_conflict.assert_called_once_with(
        f'sender nonce {mocked_load().nonce} is not unique')
    assert response.status_code == 406


@unittest.mock.patch('pantos.servicenode.restapi.not_acceptable')
@unittest.mock.patch.object(
    TransferInteractor, 'initiate_transfer',
    side_effect=TransferInteractorBidNotAcceptedError('bid not accepted'))
@unittest.mock.patch.object(_TransferSchema, 'load')
def test_transfer_bid_not_accepted_error(mocked_load, mocked_initiate_transfer,
                                         mocked_not_acceptable, test_client,
                                         initiate_transfer_request):
    mocked_load.return_value = initiate_transfer_request

    mocked_not_acceptable.side_effect = \
        lambda error_message: flask_restful.abort(  # noqa: E731
            406, message=error_message)

    response = test_client.post('/transfer', json={})

    assert response.status_code == 406
    mocked_not_acceptable.assert_called_once()


@unittest.mock.patch('pantos.servicenode.restapi.internal_server_error')
@unittest.mock.patch.object(_TransferSchema, 'load', side_effect=Exception)
def test_transfer_exception(mocked_load, mocked_internal_server_error,
                            test_client):
    mocked_internal_server_error.side_effect = \
        lambda error_message: flask_restful.abort(  # noqa: E731
            406, message=error_message)

    response = test_client.post('/transfer', json={})

    mocked_internal_server_error.assert_called_once_with()
    assert response.status_code == 500
