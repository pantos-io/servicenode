import unittest.mock

import marshmallow
import pytest

from pantos.common.blockchains.enums import Blockchain
from pantos.servicenode.restapi import _TransferSchema


@unittest.mock.patch('pantos.servicenode.restapi.get_blockchain_config',
                     return_value={'active': True})
@unittest.mock.patch('pantos.servicenode.restapi.get_blockchain_client')
def test_transfer_schema_correct(mocked_blockchain_client,
                                 mocked_get_blockchain_config,
                                 source_blockchain, destination_blockchain,
                                 sender_address, source_token_address,
                                 destination_token_address, bid_id, fee,
                                 valid_until, time_received, transfer_request,
                                 initiate_transfer_request):
    mocked_blockchain_client().is_valid_address.return_value = True
    mocked_blockchain_client().is_valid_recipient_address.return_value = True
    is_valid_address_calls = [
        unittest.mock.call(sender_address),
        unittest.mock.call(source_token_address),
        unittest.mock.call(destination_token_address)
    ]

    request = _TransferSchema().load(transfer_request)

    mocked_get_blockchain_config.assert_called_once_with(source_blockchain)
    mocked_blockchain_client().is_valid_address.assert_has_calls(
        is_valid_address_calls)
    assert request == initiate_transfer_request


def test_transfer_schema_source_blockchain_id_not_in_supported(
        invalid_blockchain_id, transfer_request):
    patcher = unittest.mock.patch.dict(
        transfer_request, {'source_blockchain_id': invalid_blockchain_id})
    patcher.start()
    supported_blockchains_ids = [blockchain.value for blockchain in Blockchain]
    expected_message = {
        'source_blockchain_id': [
            'This is not a supported blockchain. '
            f'Must be one of: {supported_blockchains_ids}.'
        ]
    }
    transfer_request['source_blockchain_id'] = invalid_blockchain_id

    with pytest.raises(marshmallow.ValidationError) as exc_info:
        _TransferSchema().load(transfer_request)

    assert exc_info.value.messages == expected_message
    patcher.stop()


@unittest.mock.patch('pantos.servicenode.restapi.get_blockchain_config',
                     return_value={'active': False})
def test_transfer_schema_source_blockchain_id_inactive(
        mocked_get_blockchain_config, transfer_request,
        inactive_blockchain_id):
    patcher = unittest.mock.patch.dict(
        transfer_request, {'source_blockchain_id': inactive_blockchain_id})
    patcher.start()
    expected_message = {
        'source_blockchain_id': ['This is not an active blockchain.']
    }
    transfer_request['source_blockchain_id'] = inactive_blockchain_id

    with pytest.raises(marshmallow.ValidationError) as exc_info:
        _TransferSchema().load(transfer_request)

    assert exc_info.value.messages == expected_message
    patcher.stop()


@unittest.mock.patch('pantos.servicenode.restapi.get_blockchain_config',
                     return_value={'active': True})
@unittest.mock.patch('pantos.servicenode.restapi.get_blockchain_client')
def test_transfer_schema_sender_address_not_valid(mocked_blockchain_client,
                                                  mocked_get_blockchain_config,
                                                  source_blockchain,
                                                  transfer_request):
    mocked_blockchain_client().is_valid_address.return_value = False

    with pytest.raises(marshmallow.ValidationError) as exc_info:
        _TransferSchema().load(transfer_request)

    expected_message = {
        'sender_address': [
            'sender address must be a valid blockchain '
            f'address on {source_blockchain.name}'
        ]
    }
    assert exc_info.value.messages == expected_message


@unittest.mock.patch('pantos.servicenode.restapi.get_blockchain_config',
                     return_value={'active': True})
@unittest.mock.patch('pantos.servicenode.restapi.get_blockchain_client')
def test_transfer_schema_recipient_address_not_valid(
        mocked_blockchain_client, mocked_get_blockchain_config,
        destination_blockchain, transfer_request):
    mocked_blockchain_client().is_valid_address.return_value = True
    mocked_blockchain_client().is_valid_recipient_address.return_value = False

    with pytest.raises(marshmallow.ValidationError) as exc_info:
        _TransferSchema().load(transfer_request)

    expected_message = {
        'recipient_address': [
            'recipient address must be a valid blockchain '
            'address, different from the 0 address on '
            f'{destination_blockchain.name}',
        ]
    }
    assert exc_info.value.messages == expected_message


@unittest.mock.patch('pantos.servicenode.restapi.get_blockchain_config',
                     return_value={'active': True})
@unittest.mock.patch('pantos.servicenode.restapi.get_blockchain_client')
def test_transfer_schema_source_token_address_not_valid(
        mocked_blockchain_client, mocked_get_blockchain_config, sender_address,
        source_token_address, transfer_request, source_blockchain):
    mocked_blockchain_client().is_valid_address.side_effect = lambda x: {
        sender_address: True,
        source_token_address: False
    }[x]
    mocked_blockchain_client().is_valid_recipient_address.return_value = True

    with pytest.raises(marshmallow.ValidationError) as exc_info:
        _TransferSchema().load(transfer_request)

    expected_message = {
        'source_token_address': [
            'source token address must be a valid blockchain '
            f'address on {source_blockchain.name}',
        ]
    }
    assert exc_info.value.messages == expected_message


@unittest.mock.patch('pantos.servicenode.restapi.get_blockchain_config',
                     return_value={'active': True})
@unittest.mock.patch('pantos.servicenode.restapi.get_blockchain_client')
def test_transfer_schema_destination_token_address_not_valid(
        mocked_blockchain_client, mocked_get_blockchain_config,
        destination_blockchain, sender_address, source_token_address,
        destination_token_address, transfer_request):
    mocked_blockchain_client().is_valid_address.side_effect = lambda x: {
        sender_address: True,
        source_token_address: True,
        destination_token_address: False
    }[x]
    mocked_blockchain_client().is_valid_recipient_address.return_value = True

    with pytest.raises(marshmallow.ValidationError) as exc_info:
        _TransferSchema().load(transfer_request)

    expected_message = {
        'destination_token_address': [
            'destination token address must be a valid blockchain '
            f'address on {destination_blockchain.name}',
        ]
    }
    assert exc_info.value.messages == expected_message


@unittest.mock.patch('pantos.servicenode.restapi.get_blockchain_config',
                     return_value={'active': True})
@unittest.mock.patch('pantos.servicenode.restapi.get_blockchain_client')
def test_transfer_schema_amount_not_valid(mocked_blockchain_client,
                                          mocked_get_blockchain_config,
                                          transfer_request):
    mocked_blockchain_client().is_valid_address.return_value = True
    mocked_blockchain_client().is_valid_recipient_address.return_value = True
    patcher = unittest.mock.patch.dict(transfer_request, {'amount': -1})
    patcher.start()

    with pytest.raises(marshmallow.ValidationError) as exc_info:
        _TransferSchema().load(transfer_request)

    expected_message = {
        'amount': [
            'amount must be greater than 0',
        ]
    }
    assert exc_info.value.messages == expected_message
    patcher.stop()
