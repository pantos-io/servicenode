import time
import unittest.mock
import uuid

import celery.exceptions  # type: ignore
import pytest
from pantos.common.blockchains.enums import Blockchain
from pantos.common.entities import TransactionStatus

from pantos.servicenode.blockchains.base import BlockchainClient
from pantos.servicenode.blockchains.base import InvalidSignatureError
from pantos.servicenode.blockchains.base import \
    UnresolvableTransferSubmissionError
from pantos.servicenode.business.bids import BidInteractorError
from pantos.servicenode.business.transfers import TransferInteractor
from pantos.servicenode.business.transfers import TransferInteractorError
from pantos.servicenode.business.transfers import \
    TransferInteractorResourceNotFoundError
from pantos.servicenode.business.transfers import \
    TransferInteractorUnrecoverableError
from pantos.servicenode.business.transfers import confirm_transfer_task
from pantos.servicenode.business.transfers import execute_transfer_task
from pantos.servicenode.database.enums import TransferStatus
from pantos.servicenode.database.exceptions import SenderNonceNotUniqueError


class MockBidPlugin:

    def accept_bid(self, bid):
        return True


@unittest.mock.patch('pantos.servicenode.business.transfers.get_bid_plugin')
@unittest.mock.patch('pantos.servicenode.business.transfers.'
                     'execute_transfer_task')
@unittest.mock.patch('pantos.servicenode.business.transfers.'
                     'database_access')
@unittest.mock.patch('pantos.servicenode.business.transfers.'
                     'get_blockchain_client')
@unittest.mock.patch('pantos.servicenode.business.transfers.'
                     'get_blockchain_config')
@unittest.mock.patch.object(TransferInteractor,
                            '_TransferInteractor__check_valid_until',
                            return_value=True)
@unittest.mock.patch.object(TransferInteractor,
                            '_TransferInteractor__check_valid_bid',
                            return_value=True)
def test_initiate_transfer_correct(
        mocked_check_valid_bid, mocked_check_valid_until,
        mocked_get_blockchain_config, mocked_get_blockchain_client,
        mocked_database_access, mocked_execute_transfer_task,
        mocked_get_bid_plugin, uuid_, initiate_transfer_request):
    mocked_get_bid_plugin.return_value = MockBidPlugin()
    mocked_execute_transfer_task.delay().id = uuid_
    get_blockchain_client_calls = [
        unittest.mock.call(initiate_transfer_request.source_blockchain),
        unittest.mock.call(initiate_transfer_request.destination_blockchain)
    ]
    task_id = TransferInteractor().initiate_transfer(initiate_transfer_request)

    assert task_id == uuid.UUID(uuid_)
    mocked_get_blockchain_config.assert_called_once_with(
        initiate_transfer_request.source_blockchain)
    mocked_get_blockchain_client.assert_has_calls(get_blockchain_client_calls)
    mocked_database_access.create_transfer.assert_called_once_with(
        initiate_transfer_request.source_blockchain,
        initiate_transfer_request.destination_blockchain,
        initiate_transfer_request.sender_address,
        initiate_transfer_request.recipient_address,
        initiate_transfer_request.source_token_address,
        initiate_transfer_request.destination_token_address,
        initiate_transfer_request.amount, initiate_transfer_request.bid.fee,
        initiate_transfer_request.nonce, initiate_transfer_request.signature,
        mocked_get_blockchain_config()['hub'],
        mocked_get_blockchain_config()['forwarder'])
    mocked_execute_transfer_task.delay.assert_called_with(
        mocked_database_access.create_transfer(),
        initiate_transfer_request.source_blockchain.value,
        initiate_transfer_request.destination_blockchain.value,
        initiate_transfer_request.sender_address,
        initiate_transfer_request.recipient_address,
        initiate_transfer_request.source_token_address,
        initiate_transfer_request.destination_token_address,
        initiate_transfer_request.amount, initiate_transfer_request.bid.fee,
        initiate_transfer_request.nonce, initiate_transfer_request.valid_until,
        initiate_transfer_request.signature)
    mocked_database_access.update_transfer_task_id.assert_called_once_with(
        mocked_database_access.create_transfer(), uuid.UUID(uuid_))


@unittest.mock.patch('pantos.servicenode.business.transfers.'
                     'get_blockchain_config')
def test_initiate_transfer_request_sender_nonce_not_unique_error(
        mocked_get_blockchain_config, source_blockchain, sender_address, nonce,
        initiate_transfer_request):
    nonce_not_unique_error = SenderNonceNotUniqueError(source_blockchain,
                                                       sender_address, nonce)
    mocked_get_blockchain_config.side_effect = nonce_not_unique_error

    with pytest.raises(SenderNonceNotUniqueError) as exc_info:
        TransferInteractor().initiate_transfer(initiate_transfer_request)

    assert exc_info.value == nonce_not_unique_error


@unittest.mock.patch('pantos.servicenode.business.transfers.get_bid_plugin')
@unittest.mock.patch('pantos.servicenode.business.transfers.'
                     'get_blockchain_client')
@unittest.mock.patch('pantos.servicenode.business.transfers.'
                     'get_blockchain_config')
@unittest.mock.patch.object(TransferInteractor,
                            '_TransferInteractor__check_valid_until')
def test_initiate_transfer_request_not_valid_until(
        mocked_check_valid_until, mocked_get_blockchain_config,
        mocked_get_blockchain_client, mocked_get_bid_plugin, source_blockchain,
        sender_address, nonce, initiate_transfer_request):

    mocked_get_bid_plugin.return_value = MockBidPlugin()
    mocked_check_valid_until.side_effect = BidInteractorError(
        message='bid has expired', field_name='bid_valid_until')

    with pytest.raises(TransferInteractorError):
        TransferInteractor().initiate_transfer(initiate_transfer_request)


@unittest.mock.patch('pantos.servicenode.business.transfers.get_bid_plugin')
@unittest.mock.patch('pantos.servicenode.business.transfers.'
                     'get_blockchain_client')
@unittest.mock.patch('pantos.servicenode.business.transfers.'
                     'get_blockchain_config')
@unittest.mock.patch.object(TransferInteractor,
                            '_TransferInteractor__check_valid_until',
                            return_value=True)
@unittest.mock.patch.object(TransferInteractor,
                            '_TransferInteractor__check_valid_bid',
                            return_value=True)
def test_initiate_transfer_request_bid_invalid(
        mocked_check_bid_valid, mocked_check_valid_until,
        mocked_get_blockchain_config, mocked_get_blockchain_client,
        mocked_get_bid_plugin, source_blockchain, sender_address, nonce,
        initiate_transfer_request):

    mocked_get_bid_plugin.return_value = MockBidPlugin()
    mocked_check_bid_valid.side_effect = BidInteractorError(
        message='bid has expired', field_name='bid_valid_until')

    with pytest.raises(TransferInteractorError):
        TransferInteractor().initiate_transfer(initiate_transfer_request)


@unittest.mock.patch(
    'pantos.servicenode.business.transfers.get_blockchain_config',
    side_effect=Exception)
def test_initiate_transfer_request_error(mocked_get_blockchain_config,
                                         initiate_transfer_request):
    with pytest.raises(Exception):
        TransferInteractor().initiate_transfer(initiate_transfer_request)


@unittest.mock.patch('pantos.servicenode.business.transfers.'
                     'database_access')
def test_find_transfer_correct(mocked_database_access, source_blockchain,
                               destination_blockchain, amount, transfer_status,
                               fee, uuid_):
    transfer = mocked_database_access.read_transfer_by_task_id()
    transfer.source_blockchain_id = source_blockchain.value
    transfer.destination_blockchain_id = destination_blockchain.value
    transfer.amount = amount
    transfer.status_id = transfer_status.value
    transfer.fee = fee
    expected_response = TransferInteractor.FindTransferResponse(
        source_blockchain, destination_blockchain, transfer.sender_address,
        transfer.recipient_address, transfer.source_token_contract.address,
        transfer.destination_token_contract.address,
        int(transfer.amount), transfer.fee, transfer_status,
        int(transfer.on_chain_transfer_id), transfer.transaction_id)

    transfer_response = TransferInteractor().find_transfer(uuid_)

    assert transfer_response == expected_response
    mocked_database_access.read_transfer_by_task_id.assert_called_with(uuid_)


@unittest.mock.patch('pantos.servicenode.business.transfers.'
                     'database_access')
def test_find_transfer_resource_not_found_error(mocked_database_access, uuid_):
    mocked_database_access.read_transfer_by_task_id.return_value = None

    with pytest.raises(TransferInteractorResourceNotFoundError):
        TransferInteractor().find_transfer(uuid_)


@unittest.mock.patch('pantos.servicenode.business.transfers.'
                     'database_access')
def test_find_transfer_error(mocked_database_access, uuid_):
    mocked_database_access.read_transfer_by_task_id.side_effect = \
        Exception()

    with pytest.raises(Exception):
        TransferInteractor().find_transfer(uuid_)


@unittest.mock.patch('pantos.servicenode.business.transfers.'
                     'time')
@unittest.mock.patch('pantos.servicenode.business.transfers.'
                     'get_blockchain_client')
@unittest.mock.patch('pantos.servicenode.business.transfers.'
                     'database_access')
def test_execute_transfer_single_chain_correct(mocked_database_access,
                                               mocked_get_blockchain_client,
                                               mocked_time,
                                               execute_transfer_request):
    mocked_time.time.return_value = execute_transfer_request.valid_until - 1
    execute_transfer_request.source_blockchain = \
        execute_transfer_request.destination_blockchain
    execute_transfer_request.source_token_address = \
        execute_transfer_request.destination_token_address
    expected_transfer_request = \
        BlockchainClient.TransferSubmissionStartRequest(
            execute_transfer_request.internal_transfer_id,
            execute_transfer_request.sender_address,
            execute_transfer_request.recipient_address,
            execute_transfer_request.source_token_address,
            execute_transfer_request.amount, execute_transfer_request.fee,
            execute_transfer_request.sender_nonce,
            execute_transfer_request.valid_until,
            execute_transfer_request.signature)

    internal_transaction_id = TransferInteractor().execute_transfer(
        execute_transfer_request)

    mocked_get_blockchain_client().start_transfer_submission.\
        assert_called_with(expected_transfer_request)
    mocked_database_access.update_transfer_status.assert_called_once_with(
        execute_transfer_request.internal_transfer_id,
        TransferStatus.SUBMITTED)
    assert (internal_transaction_id == mocked_get_blockchain_client().
            start_transfer_submission(expected_transfer_request))


@unittest.mock.patch('pantos.servicenode.business.transfers.'
                     'time')
@unittest.mock.patch('pantos.servicenode.business.transfers.'
                     'database_access')
def test_execute_transfer_single_chain_source_and_destination_token_error(
        mocked_database_access, mocked_time, execute_transfer_request):
    mocked_time.time.return_value = execute_transfer_request.valid_until - 1
    execute_transfer_request.source_blockchain = \
        execute_transfer_request.destination_blockchain

    with pytest.raises(TransferInteractorUnrecoverableError):
        TransferInteractor().execute_transfer(execute_transfer_request)

    mocked_database_access.update_transfer_status.assert_called_once_with(
        execute_transfer_request.internal_transfer_id, TransferStatus.FAILED)


@unittest.mock.patch('pantos.servicenode.business.transfers.'
                     'time')
@unittest.mock.patch('pantos.servicenode.business.transfers.'
                     'get_blockchain_client')
@unittest.mock.patch('pantos.servicenode.business.transfers.'
                     'database_access')
def test_execute_transfer_single_chain_unrecoverable_error(
        mocked_database_access, mocked_get_blockchain_client, mocked_time,
        execute_transfer_request):
    mocked_time.time.return_value = execute_transfer_request.valid_until - 1
    mocked_get_blockchain_client().start_transfer_submission.side_effect = \
        InvalidSignatureError
    execute_transfer_request.source_blockchain = \
        execute_transfer_request.destination_blockchain
    execute_transfer_request.source_token_address = \
        execute_transfer_request.destination_token_address

    with pytest.raises(TransferInteractorUnrecoverableError):
        TransferInteractor().execute_transfer(execute_transfer_request)

    mocked_database_access.update_transfer_status.assert_called_once_with(
        execute_transfer_request.internal_transfer_id, TransferStatus.FAILED)


@unittest.mock.patch('pantos.servicenode.business.transfers.'
                     'time')
@unittest.mock.patch('pantos.servicenode.business.transfers.'
                     'get_blockchain_client')
@unittest.mock.patch('pantos.servicenode.business.transfers.'
                     'database_access')
def test_execute_transfer_single_chain_error(mocked_database_access,
                                             mocked_get_blockchain_client,
                                             mocked_time,
                                             execute_transfer_request):
    mocked_time.time.return_value = execute_transfer_request.valid_until - 1
    mocked_get_blockchain_client().start_transfer_submission.side_effect = \
        Exception
    execute_transfer_request.source_blockchain = \
        execute_transfer_request.destination_blockchain
    execute_transfer_request.source_token_address = \
        execute_transfer_request.destination_token_address

    with pytest.raises(Exception):
        TransferInteractor().execute_transfer(execute_transfer_request)

    mocked_database_access.update_transfer_status.assert_called_once_with(
        execute_transfer_request.internal_transfer_id, TransferStatus.ACCEPTED)


@unittest.mock.patch('pantos.servicenode.business.transfers.'
                     'time')
@unittest.mock.patch('pantos.servicenode.business.transfers.'
                     'get_blockchain_client')
@unittest.mock.patch('pantos.servicenode.business.transfers.'
                     'database_access')
def test_execute_transfer_cross_chain_correct(mocked_database_access,
                                              mocked_get_blockchain_client,
                                              mocked_time,
                                              execute_transfer_request):
    mocked_time.time.return_value = execute_transfer_request.valid_until - 1
    expected_transfer_from_request = \
        BlockchainClient.TransferFromSubmissionStartRequest(
            execute_transfer_request.internal_transfer_id,
            execute_transfer_request.destination_blockchain,
            execute_transfer_request.sender_address,
            execute_transfer_request.recipient_address,
            execute_transfer_request.source_token_address,
            execute_transfer_request.destination_token_address,
            execute_transfer_request.amount, execute_transfer_request.fee,
            execute_transfer_request.sender_nonce,
            execute_transfer_request.valid_until,
            execute_transfer_request.signature)

    internal_transaction_id = TransferInteractor().execute_transfer(
        execute_transfer_request)

    mocked_get_blockchain_client().start_transfer_from_submission.\
        assert_called_with(expected_transfer_from_request)
    mocked_database_access.update_transfer_status.assert_called_once_with(
        execute_transfer_request.internal_transfer_id,
        TransferStatus.SUBMITTED)
    assert (internal_transaction_id == mocked_get_blockchain_client().
            start_transfer_from_submission(expected_transfer_from_request))


@unittest.mock.patch('pantos.servicenode.business.transfers.'
                     'time')
@unittest.mock.patch('pantos.servicenode.business.transfers.'
                     'get_blockchain_client')
@unittest.mock.patch('pantos.servicenode.business.transfers.'
                     'database_access')
def test_execute_transfer_cross_chain_unrecoverable_error(
        mocked_database_access, mocked_get_blockchain_client, mocked_time,
        execute_transfer_request):
    mocked_time.time.return_value = execute_transfer_request.valid_until - 1
    mocked_get_blockchain_client().start_transfer_from_submission.\
        side_effect = InvalidSignatureError

    with pytest.raises(TransferInteractorUnrecoverableError):
        TransferInteractor().execute_transfer(execute_transfer_request)

    mocked_database_access.update_transfer_status.assert_called_once_with(
        execute_transfer_request.internal_transfer_id, TransferStatus.FAILED)


@unittest.mock.patch('pantos.servicenode.business.transfers.'
                     'time')
@unittest.mock.patch('pantos.servicenode.business.transfers.'
                     'database_access')
def test_execute_transfer_validity_expired_unrecoverable_error(
        mocked_database_access, mocked_time, execute_transfer_request):
    mocked_time.time.return_value = execute_transfer_request.valid_until + 1

    with pytest.raises(TransferInteractorUnrecoverableError):
        TransferInteractor().execute_transfer(execute_transfer_request)

    mocked_database_access.update_transfer_status.assert_called_once_with(
        execute_transfer_request.internal_transfer_id, TransferStatus.FAILED)


@unittest.mock.patch('pantos.servicenode.business.transfers.'
                     'get_blockchain_client')
@unittest.mock.patch('pantos.servicenode.business.transfers.'
                     'database_access')
def test_confirm_transfer_confirmed_correct(mocked_database_access,
                                            mocked_get_blockchain_client,
                                            confirm_transfer_request,
                                            transaction_id,
                                            transfer_on_chain_id):
    status_response = BlockchainClient.TransferSubmissionStatusResponse(
        True,
        transaction_status=TransactionStatus.CONFIRMED,
        transaction_id=transaction_id,
        on_chain_transfer_id=transfer_on_chain_id)
    mocked_get_blockchain_client().get_transfer_submission_status.\
        return_value = status_response

    is_finished = TransferInteractor().confirm_transfer(
        confirm_transfer_request)

    assert is_finished
    mocked_get_blockchain_client().get_transfer_submission_status.\
        assert_called_with(
            confirm_transfer_request.internal_transaction_id,
            confirm_transfer_request.destination_blockchain)
    mocked_database_access.update_transfer_transaction_id.\
        assert_called_once_with(
            confirm_transfer_request.internal_transfer_id,
            transaction_id)
    mocked_database_access.update_on_chain_transfer_id.assert_called_once_with(
        confirm_transfer_request.internal_transfer_id, transfer_on_chain_id)
    mocked_database_access.update_transfer_status.assert_called_once_with(
        confirm_transfer_request.internal_transfer_id,
        TransferStatus.CONFIRMED)


@unittest.mock.patch('pantos.servicenode.business.transfers.'
                     'get_blockchain_client')
@unittest.mock.patch('pantos.servicenode.business.transfers.'
                     'database_access')
def test_confirm_transfer_unconfirmed_correct(mocked_database_access,
                                              mocked_get_blockchain_client,
                                              confirm_transfer_request):
    status_response = BlockchainClient.TransferSubmissionStatusResponse(False)
    mocked_get_blockchain_client().get_transfer_submission_status.\
        return_value = status_response

    is_finished = TransferInteractor().confirm_transfer(
        confirm_transfer_request)

    assert not is_finished
    mocked_get_blockchain_client().get_transfer_submission_status.\
        assert_called_with(
            confirm_transfer_request.internal_transaction_id,
            confirm_transfer_request.destination_blockchain)


@unittest.mock.patch('pantos.servicenode.business.transfers.'
                     'get_blockchain_client')
@unittest.mock.patch('pantos.servicenode.business.transfers.'
                     'database_access')
def test_confirm_transfer_reverted_correct(mocked_database_access,
                                           mocked_get_blockchain_client,
                                           confirm_transfer_request,
                                           transaction_id):
    status_response = BlockchainClient.TransferSubmissionStatusResponse(
        True,
        transaction_status=TransactionStatus.REVERTED,
        transaction_id=transaction_id)
    mocked_get_blockchain_client().get_transfer_submission_status.\
        return_value = status_response

    is_finished = TransferInteractor().confirm_transfer(
        confirm_transfer_request)

    assert is_finished
    mocked_get_blockchain_client().get_transfer_submission_status.\
        assert_called_with(
            confirm_transfer_request.internal_transaction_id,
            confirm_transfer_request.destination_blockchain)
    mocked_database_access.update_transfer_status.assert_called_once_with(
        confirm_transfer_request.internal_transfer_id, TransferStatus.REVERTED)


@unittest.mock.patch('pantos.servicenode.business.transfers.'
                     'get_blockchain_client')
@unittest.mock.patch('pantos.servicenode.business.transfers.'
                     'database_access')
def test_confirm_transfer_unresolvable_submission_error(
        mocked_database_access, mocked_get_blockchain_client,
        confirm_transfer_request):
    mocked_get_blockchain_client().get_transfer_submission_status.\
        side_effect = UnresolvableTransferSubmissionError

    is_finished = TransferInteractor().confirm_transfer(
        confirm_transfer_request)

    assert is_finished
    mocked_get_blockchain_client().get_transfer_submission_status.\
        assert_called_with(
            confirm_transfer_request.internal_transaction_id,
            confirm_transfer_request.destination_blockchain)
    mocked_database_access.reset_transfer_nonce.assert_called_once_with(
        confirm_transfer_request.internal_transfer_id)
    mocked_database_access.update_transfer_status.assert_called_once_with(
        confirm_transfer_request.internal_transfer_id, TransferStatus.FAILED)


@unittest.mock.patch(
    'pantos.servicenode.business.transfers.get_blockchain_client',
    side_effect=Exception())
def test_confirm_transfer_error(mocked_get_blockchain_client,
                                confirm_transfer_request):
    with pytest.raises(TransferInteractorError):
        TransferInteractor().confirm_transfer(confirm_transfer_request)


@unittest.mock.patch('pantos.servicenode.business.transfers.config')
@unittest.mock.patch(
    'pantos.servicenode.business.transfers.confirm_transfer_task')
@unittest.mock.patch.object(TransferInteractor, 'execute_transfer')
def test_execute_transfer_task_correct(
        mocked_execute_transfer, mocked_confirm_task, mocked_config,
        confirm_retry_interval, transfer_internal_id, source_blockchain,
        destination_blockchain, sender_address, recipient_address,
        source_token_address, destination_token_address, amount, fee, nonce,
        valid_until, signature):
    mocked_config_dict = {
        'tasks': {
            'confirm_transfer': {
                'interval': confirm_retry_interval
            }
        }
    }
    mocked_config.__getitem__.side_effect = mocked_config_dict.__getitem__
    expected_execute_transfer_request = \
        TransferInteractor.ExecuteTransferRequest(
            transfer_internal_id, source_blockchain, destination_blockchain,
            sender_address, recipient_address, source_token_address,
            destination_token_address, amount, fee, nonce, valid_until,
            signature)

    result = execute_transfer_task(
        transfer_internal_id, source_blockchain.value,
        destination_blockchain.value, sender_address, recipient_address,
        source_token_address, destination_token_address, amount, fee, nonce,
        valid_until, signature)

    assert result is True
    mocked_execute_transfer.assert_called_once_with(
        expected_execute_transfer_request)
    mocked_confirm_task.apply_async.assert_called_once_with(
        args=(transfer_internal_id, source_blockchain.value,
              destination_blockchain.value,
              str(mocked_execute_transfer(expected_execute_transfer_request))),
        countdown=confirm_retry_interval)


@unittest.mock.patch('pantos.servicenode.business.transfers.config')
@unittest.mock.patch.object(
    TransferInteractor,
    'execute_transfer',
    side_effect=TransferInteractorUnrecoverableError(''))
def test_execute_transfer_task_unrecoverable_error(
        mocked_execute_transfer, transfer_internal_id, source_blockchain,
        destination_blockchain, sender_address, recipient_address,
        source_token_address, destination_token_address, amount, fee, nonce,
        valid_until, signature):

    result = execute_transfer_task(
        transfer_internal_id, source_blockchain.value,
        destination_blockchain.value, sender_address, recipient_address,
        source_token_address, destination_token_address, amount, fee, nonce,
        valid_until, signature)

    assert result is False


@unittest.mock.patch('pantos.servicenode.business.transfers.config')
@unittest.mock.patch(
    'pantos.servicenode.business.transfers.execute_transfer_task.retry',
    return_value=celery.exceptions.RetryTaskError())
@unittest.mock.patch.object(TransferInteractor, 'execute_transfer')
def test_execute_transfer_task_error(
        mocked_execute_transfer, mocked_execute_task_retry, mocked_config,
        execute_retry_interval, transfer_internal_id, source_blockchain,
        destination_blockchain, sender_address, recipient_address,
        source_token_address, destination_token_address, amount, fee, nonce,
        valid_until, signature):
    transfer_interactor_error = TransferInteractorError('')
    mocked_execute_transfer.side_effect = transfer_interactor_error
    mocked_config_dict = {
        'tasks': {
            'execute_transfer': {
                'retry_interval_after_error': execute_retry_interval
            }
        }
    }
    mocked_config.__getitem__.side_effect = mocked_config_dict.__getitem__

    with pytest.raises(celery.exceptions.RetryTaskError):
        execute_transfer_task(transfer_internal_id, source_blockchain.value,
                              destination_blockchain.value, sender_address,
                              recipient_address, source_token_address,
                              destination_token_address, amount, fee, nonce,
                              valid_until, signature)

    mocked_execute_task_retry.assert_called_once_with(
        countdown=execute_retry_interval, exc=transfer_interactor_error)


@unittest.mock.patch.object(TransferInteractor, 'confirm_transfer')
def test_confirm_transfer_task_correct(mocked_confirm_transfer,
                                       transfer_internal_id, source_blockchain,
                                       destination_blockchain,
                                       internal_transaction_id):
    mocked_confirm_transfer.return_value = True
    expected_confirm_transfer_request = \
        TransferInteractor.ConfirmTransferRequest(
            transfer_internal_id, source_blockchain, destination_blockchain,
            internal_transaction_id)

    result = confirm_transfer_task(transfer_internal_id,
                                   source_blockchain.value,
                                   destination_blockchain.value,
                                   str(internal_transaction_id))

    assert result is True
    mocked_confirm_transfer.assert_called_once_with(
        expected_confirm_transfer_request)


@unittest.mock.patch(
    'pantos.servicenode.business.transfers.confirm_transfer_task.retry',
    return_value=celery.exceptions.RetryTaskError())
@unittest.mock.patch('pantos.servicenode.business.transfers.config')
@unittest.mock.patch.object(TransferInteractor, 'confirm_transfer')
def test_confirm_transfer_task_confirmation_not_completed(
        mocked_confirm_transfer, mocked_config, mocked_retry,
        confirm_retry_interval, transfer_internal_id, source_blockchain,
        destination_blockchain, internal_transaction_id):
    mocked_config_dict = {
        'tasks': {
            'confirm_transfer': {
                'interval': confirm_retry_interval
            }
        }
    }
    mocked_config.__getitem__.side_effect = mocked_config_dict.__getitem__
    mocked_confirm_transfer.return_value = False

    with pytest.raises(celery.exceptions.RetryTaskError):
        confirm_transfer_task(transfer_internal_id, source_blockchain.value,
                              destination_blockchain.value,
                              str(internal_transaction_id))

    mocked_retry.assert_called_once_with(countdown=confirm_retry_interval)


@unittest.mock.patch(
    'pantos.servicenode.business.transfers.confirm_transfer_task.retry',
    return_value=celery.exceptions.RetryTaskError())
@unittest.mock.patch('pantos.servicenode.business.transfers.config')
@unittest.mock.patch.object(TransferInteractor, 'confirm_transfer')
def test_confirm_transfer_task_confirmation_error(
        mocked_confirm_transfer, mocked_config, mocked_retry,
        confirm_retry_interval_after_err, transfer_internal_id,
        source_blockchain, destination_blockchain, internal_transaction_id):
    confirm_transfer_error = Exception()
    mocked_confirm_transfer.side_effect = confirm_transfer_error
    mocked_config_dict = {
        'tasks': {
            'confirm_transfer': {
                'retry_interval_after_error': confirm_retry_interval_after_err
            }
        }
    }
    mocked_config.__getitem__.side_effect = mocked_config_dict.__getitem__

    with pytest.raises(celery.exceptions.RetryTaskError):
        confirm_transfer_task(transfer_internal_id, source_blockchain.value,
                              destination_blockchain.value,
                              str(internal_transaction_id))
    mocked_retry.assert_called_once_with(
        countdown=confirm_retry_interval_after_err, exc=confirm_transfer_error)


@unittest.mock.patch.object(
    TransferInteractor,
    '_TransferInteractor__is_valid_execution_time_limit',
    return_value=True)
def test_check_valid_until_correct(mocked_is_valid_execution_time_limit,
                                   source_blockchain, valid_until,
                                   bid_execution_time, time_received):
    TransferInteractor()._TransferInteractor__check_valid_until(
        source_blockchain, valid_until, bid_execution_time, time_received)


@unittest.mock.patch.object(
    TransferInteractor,
    '_TransferInteractor__is_valid_execution_time_limit',
    return_value=False)
def test_check_valid_until_invalid(mocked_is_valid_execution_time_limit,
                                   source_blockchain, valid_until,
                                   bid_execution_time, time_received):
    with pytest.raises(TransferInteractorError):
        TransferInteractor()._TransferInteractor__check_valid_until(
            source_blockchain, valid_until, bid_execution_time, time_received)


@unittest.mock.patch.object(TransferInteractor,
                            '_TransferInteractor__has_bid_expired',
                            return_value=False)
@unittest.mock.patch.object(TransferInteractor,
                            '_TransferInteractor__verify_bids_signature',
                            return_value=True)
def test_check_valid_bid_correct(mocked_has_bid_expired,
                                 mocked_verify_bids_signature, bid,
                                 source_blockchain, destination_blockchain):
    TransferInteractor()._TransferInteractor__check_valid_bid(
        bid, source_blockchain, destination_blockchain)


@unittest.mock.patch.object(TransferInteractor,
                            '_TransferInteractor__has_bid_expired',
                            return_value=True)
def test_check_valid_bid_expired(mocked_has_bid_expired, bid,
                                 source_blockchain, destination_blockchain):
    with pytest.raises(TransferInteractorError):
        TransferInteractor()._TransferInteractor__check_valid_bid(
            bid, source_blockchain, destination_blockchain)


@unittest.mock.patch.object(TransferInteractor,
                            '_TransferInteractor__has_bid_expired',
                            return_value=False)
@unittest.mock.patch.object(TransferInteractor,
                            '_TransferInteractor__verify_bids_signature',
                            return_value=False)
def test_check_valid_bid_invalid_signature(mocked_has_bid_expired,
                                           mocked_verify_bids_signature, bid,
                                           source_blockchain,
                                           destination_blockchain):
    with pytest.raises(TransferInteractorError):
        TransferInteractor()._TransferInteractor__check_valid_bid(
            bid, source_blockchain, destination_blockchain)


@pytest.mark.parametrize("bid_vaild_until,expected",
                         [(time.time() - 2, True), (time.time() * 2, False)])
def test_has_bid_expired(bid_vaild_until, expected):
    assert TransferInteractor()._TransferInteractor__has_bid_expired(
        bid_vaild_until) is expected


@unittest.mock.patch('pantos.servicenode.business.transfers.get_signer')
@unittest.mock.patch('pantos.servicenode.business.transfers.get_signer_config')
def test_verify_bids_signature(mocked_get_signer_config, mocked_get_signer):
    fee = 0
    bid_valid_until = time.time() * 2
    valid_until = 0
    source_blockchain_id = 0
    destination_blockchain_id = 0
    bid_signature = 'sig'

    mocked_get_signer.return_value.verify_message.return_value = True
    assert TransferInteractor()._TransferInteractor__verify_bids_signature(
        fee, bid_valid_until, valid_until, source_blockchain_id,
        destination_blockchain_id, bid_signature) is True


def test_check_valid_bid_mismatch(bid, source_blockchain,
                                  destination_blockchain):
    with pytest.raises(TransferInteractorError):
        TransferInteractor()._TransferInteractor__check_valid_bid(
            bid, source_blockchain, Blockchain.CELO)

    with pytest.raises(TransferInteractorError):
        TransferInteractor()._TransferInteractor__check_valid_bid(
            bid, Blockchain.CELO, destination_blockchain)

    with pytest.raises(TransferInteractorError):
        TransferInteractor()._TransferInteractor__check_valid_bid(
            bid, Blockchain.CELO, Blockchain.POLYGON)
