"""Module for Ethereum-specific clients and errors.

"""
import json
import logging
import typing
import uuid

import web3
import web3.contract.contract
import web3.exceptions
from pantos.common.blockchains.base import NodeConnections
from pantos.common.blockchains.base import TransactionNonceTooLowError
from pantos.common.blockchains.base import TransactionUnderpricedError
from pantos.common.blockchains.enums import Blockchain
from pantos.common.blockchains.ethereum import EthereumUtilities
from pantos.common.types import BlockchainAddress

from pantos.servicenode.blockchains.base import BlockchainClient
from pantos.servicenode.blockchains.base import BlockchainClientError
from pantos.servicenode.database import access as database_access

_HUB_REGISTER_SERVICE_NODE_FUNCTION_SELECTOR = '0x901428b0'
_HUB_REGISTER_SERVICE_NODE_GAS = 300000

_HUB_TRANSFER_FUNCTION_SELECTOR = '0x87d28cd6'
_HUB_TRANSFER_GAS = 200000
_HUB_VERIFY_TRANSFER_FUNCTION_NAME = 'verifyTransfer'

_HUB_TRANSFER_FROM_FUNCTION_SELECTOR = '0xa6d856e0'
_HUB_TRANSFER_FROM_GAS = 250000
_HUB_VERIFY_TRANSFER_FROM_FUNCTION_NAME = 'verifyTransferFrom'

_HUB_UNREGISTER_SERVICE_NODE_FUNCTION_SELECTOR = '0xa35a278d'
_HUB_UNREGISTER_SERVICE_NODE_GAS = 250000

_HUB_CANCEL_SERVICE_NODE_UNREGISTRATION_FUNCTION_SELECTOR = '0x13cad693'
_HUB_CANCEL_SERVICE_NODE_UNREGISTRATION_GAS = 250000

_HUB_UPDATE_SERVICE_NODE_URL_FUNCTION_SELECTOR = '0x4bbfe4f6'
_HUB_UPDATE_SERVICE_NODE_URL_GAS = 250000

_TOKEN_APPROVE_FUNCTION_SELECTOR = '0x095ea7b3'
_TOKEN_APPROVE_GAS = 100000

_INSUFFICIENT_BALANCE_ERROR = 'PantosHub: insufficient balance of sender'
_INVALID_SIGNATURE_ERROR = 'PantosForwarder: invalid signature'

_logger = logging.getLogger(__name__)


class EthereumClientError(BlockchainClientError):
    """Exception class for all Ethereum client errors.

    """
    pass


class EthereumClient(BlockchainClient):
    """Ethereum-specific blockchain client.

    """
    def __init__(self):
        # Docstring inherited
        super().__init__()
        private_key = self._get_config()['private_key']
        private_key_password = self._get_config()['private_key_password']
        private_key = self._get_utilities().decrypt_private_key(
            private_key, private_key_password)
        self.__address = self._get_utilities().get_address(private_key)

    @classmethod
    def get_blockchain(cls) -> Blockchain:
        # Docstring inherited
        return Blockchain.ETHEREUM

    @classmethod
    def get_error_class(cls) -> type[BlockchainClientError]:
        # Docstring inherited
        return EthereumClientError

    def is_node_registered(self) -> bool:
        # Docstring inherited
        try:
            node_connections = self.__create_node_connections()
            hub_contract = self._create_hub_contract(node_connections)
            node_record = hub_contract.functions.getServiceNodeRecord(
                self.__address).call().get()
            assert len(node_record) == 5
            active = node_record[0]
            assert isinstance(active, bool)
            return active
        except Exception:
            raise self._create_error(
                'unable to determine if the service node is registered')

    def is_valid_recipient_address(self, recipient_address: str) -> bool:
        # Docstring inherited
        if not self.is_valid_address(recipient_address):
            return False
        is_zero_address = int(recipient_address, 0) == 0
        return not is_zero_address

    def read_node_url(self) -> str:
        # Docstring inherited
        try:
            node_connections = self.__create_node_connections()
            hub_contract = self._create_hub_contract(node_connections)
            node_record = hub_contract.functions.getServiceNodeRecord(
                self.__address).call().get()
            assert len(node_record) == 5
            node_url = node_record[1]
            assert isinstance(node_url, str)
            return node_url
        except Exception:
            raise self._create_error('unable to read the service node URL')

    def register_node(self, node_url: str, node_deposit: int,
                      withdrawal_address: BlockchainAddress) -> None:
        # Docstring inherited
        extra_info = {
            'blockchain': self.get_blockchain(),
            'service_node_address': self.__address,
            'node_url': node_url,
            'node_deposit': node_deposit,
            'withdrawal_address': withdrawal_address
        }
        try:
            node_connections = self.__create_node_connections()
            nonce = node_connections.eth.get_transaction_count(
                self.__address).get()
            if node_deposit > 0:
                spender_address = self._get_config()['hub']
                request = BlockchainClient._TransactionSubmissionStartRequest(
                    self._versioned_pantos_token_abi,
                    _TOKEN_APPROVE_FUNCTION_SELECTOR,
                    (spender_address, node_deposit), _TOKEN_APPROVE_GAS, None,
                    nonce)
                internal_transaction_id = self._start_transaction_submission(
                    request, node_connections)
                extra_info |= {
                    'internal_transaction_id': internal_transaction_id
                }
                _logger.info('node deposit allowance submitted',
                             extra=extra_info)
                nonce += 1
            request = BlockchainClient._TransactionSubmissionStartRequest(
                self._versioned_pantos_hub_abi,
                _HUB_REGISTER_SERVICE_NODE_FUNCTION_SELECTOR,
                (self.__address, node_url, node_deposit, withdrawal_address),
                _HUB_REGISTER_SERVICE_NODE_GAS, None, nonce)
            internal_transaction_id = self._start_transaction_submission(
                request, node_connections)
            extra_info |= {'internal_transaction_id': internal_transaction_id}
            _logger.info('node registration submitted', extra=extra_info)
        except Exception:
            raise self._create_error('unable to register the service node',
                                     node_url=node_url,
                                     node_deposit=node_deposit)

    def start_transfer_submission(
            self, request: BlockchainClient.TransferSubmissionStartRequest) \
            -> uuid.UUID:
        # Docstring inherited
        on_chain_request = (request.sender_address, request.recipient_address,
                            request.token_address, request.amount,
                            self.__address, request.fee, request.sender_nonce,
                            request.valid_until)
        try:
            return self.__start_transfer_submission(
                request.internal_transfer_id, on_chain_request,
                request.signature, _HUB_VERIFY_TRANSFER_FUNCTION_NAME,
                _HUB_TRANSFER_FUNCTION_SELECTOR, _HUB_TRANSFER_GAS)
        except EthereumClientError:
            raise
        except Exception:
            raise self._create_error('unable to start a transfer submission',
                                     request=request)

    def start_transfer_from_submission(
            self,
            request: BlockchainClient.TransferFromSubmissionStartRequest) \
            -> uuid.UUID:
        # Docstring inherited
        on_chain_request = (request.destination_blockchain.value,
                            request.sender_address, request.recipient_address,
                            request.source_token_address,
                            request.destination_token_address, request.amount,
                            self.__address, request.fee, request.sender_nonce,
                            request.valid_until)
        try:
            return self.__start_transfer_submission(
                request.internal_transfer_id, on_chain_request,
                request.signature, _HUB_VERIFY_TRANSFER_FROM_FUNCTION_NAME,
                _HUB_TRANSFER_FROM_FUNCTION_SELECTOR, _HUB_TRANSFER_FROM_GAS)
        except EthereumClientError:
            raise
        except Exception:
            raise self._create_error(
                'unable to start a transferFrom submission', request=request)

    def unregister_node(self) -> None:
        # Docstring inherited
        extra_info: dict[str, typing.Any] = {
            'blockchain': self.get_blockchain(),
            'service_node_address': self.__address
        }
        try:
            node_connections = self.__create_node_connections()
            nonce = node_connections.eth.get_transaction_count(
                self.__address).get()
            request = BlockchainClient._TransactionSubmissionStartRequest(
                self._versioned_pantos_hub_abi,
                _HUB_UNREGISTER_SERVICE_NODE_FUNCTION_SELECTOR,
                (self.__address, ), _HUB_UNREGISTER_SERVICE_NODE_GAS, None,
                nonce)
            internal_transaction_id = self._start_transaction_submission(
                request, node_connections)
            extra_info |= {'internal_transaction_id': internal_transaction_id}
            _logger.info('node unregistration submitted', extra=extra_info)
        except Exception:
            raise self._create_error('unable to unregister the service node')

    def update_node_url(self, node_url: str) -> None:
        # Docstring inherited
        extra_info = {
            'blockchain': self.get_blockchain(),
            'node_url': node_url
        }
        try:
            node_connections = self.__create_node_connections()
            nonce = node_connections.eth.get_transaction_count(
                self.__address).get()
            request = BlockchainClient._TransactionSubmissionStartRequest(
                self._versioned_pantos_hub_abi,
                _HUB_UPDATE_SERVICE_NODE_URL_FUNCTION_SELECTOR, (node_url, ),
                _HUB_UPDATE_SERVICE_NODE_URL_GAS, None, nonce)
            internal_transaction_id = self._start_transaction_submission(
                request, node_connections)
            extra_info |= {'internal_transaction_id': internal_transaction_id}
            _logger.info('node URL update submitted', extra=extra_info)
        except Exception:
            raise self._create_error('unable to update the service node URL',
                                     node_url=node_url)

    def is_unbonding(self) -> bool:
        # Docstring inherited
        try:
            node_connections = self.__create_node_connections()
            hub_contract = self._create_hub_contract(node_connections)
            return hub_contract.functions.isServiceNodeInTheUnbondingPeriod(
                self.__address).call().get()
        except Exception:
            raise self._create_error(
                'unable to determine if the service node is unbonding')

    def cancel_unregistration(self) -> None:
        # Docstring inherited
        extra_info: dict[str, typing.Any] = {
            'blockchain': self.get_blockchain(),
            'service_node_address': self.__address
        }
        try:
            node_connections = self.__create_node_connections()
            nonce = node_connections.eth.get_transaction_count(
                self.__address).get()
            request = BlockchainClient._TransactionSubmissionStartRequest(
                self._versioned_pantos_hub_abi,
                _HUB_CANCEL_SERVICE_NODE_UNREGISTRATION_FUNCTION_SELECTOR,
                (self.__address, ),
                _HUB_CANCEL_SERVICE_NODE_UNREGISTRATION_GAS, None, nonce)
            internal_transaction_id = self._start_transaction_submission(
                request, node_connections)
            extra_info |= {'internal_transaction_id': internal_transaction_id}
            _logger.info('node cancel unregistration submitted',
                         extra=extra_info)
        except Exception:
            raise self._create_error(
                'unable to cancel the service node unregistration')

    def get_validator_fee_factor(self, blockchain: Blockchain) -> int:
        # Docstring inherited
        try:
            node_connections = self.__create_node_connections()
            hub_contract = self._create_hub_contract(node_connections)
            fee_factor = hub_contract.functions.getCurrentValidatorFeeFactor(
                blockchain.value).call().get()
            assert isinstance(fee_factor, int)
            return fee_factor
        except Exception:
            raise self._create_error('unable to get the validator fee factor')

    def _create_hub_contract(
            self, node_connections: NodeConnections) \
            -> NodeConnections.Wrapper[web3.contract.Contract]:
        return self._get_utilities().create_contract(
            BlockchainAddress(self._get_config()['hub']),
            self._versioned_pantos_hub_abi, node_connections)

    def _get_utilities(self) -> EthereumUtilities:
        # Docstring inherited
        return typing.cast(EthereumUtilities, super()._get_utilities())

    def _read_on_chain_transfer_id(self, transaction_id: str,
                                   destination_blockchain: Blockchain) -> int:
        # Docstring inherited
        try:
            node_connections = self.__create_node_connections()
            transaction_receipt = node_connections.eth.get_transaction_receipt(
                typing.cast(web3.types.HexStr, transaction_id)).get()
            assert (transaction_receipt['transactionHash'].to_0x_hex() ==
                    transaction_id)
            _logger.info(
                'transfer/transferFrom transaction receipt',
                extra=json.loads(web3.Web3.to_json(transaction_receipt)))
            hub_contract = self._create_hub_contract(node_connections)
            if self.get_blockchain() is destination_blockchain:
                event = hub_contract.events.TransferSucceeded()
                event_log = event.process_receipt(
                    transaction_receipt, errors=web3.logs.DISCARD)[0].get()
                on_chain_transfer_id = event_log['args']['transferId']
            else:
                event = hub_contract.events.TransferFromSucceeded()
                event_log = event.process_receipt(
                    transaction_receipt, errors=web3.logs.DISCARD)[0].get()
                on_chain_transfer_id = event_log['args']['sourceTransferId']
            return on_chain_transfer_id
        except Exception:
            raise self._create_error(
                'unable to read the Pantos transfer ID on the source '
                'blockchain', transaction_id=transaction_id,
                destination_blockchain=destination_blockchain)

    def __create_node_connections(self) -> NodeConnections:
        provider_timeout = self._get_config()['provider_timeout']
        return self._get_utilities().create_node_connections(provider_timeout)

    def __get_nonce(self, node_connections: NodeConnections,
                    internal_transfer_id: int) -> int:
        transaction_count = node_connections.eth.get_transaction_count(
            self.__address).get_maximum_result()
        database_access.update_transfer_nonce(internal_transfer_id,
                                              self.get_blockchain(),
                                              transaction_count)
        nonce = database_access.read_transfer_nonce(internal_transfer_id)
        assert nonce is not None
        return nonce

    def __start_transfer_submission(self, internal_transfer_id: int,
                                    on_chain_request: tuple, signature: str,
                                    verify_function_name: str,
                                    function_selector: str,
                                    gas: int) -> uuid.UUID:
        node_connections = self.__create_node_connections()
        hub_contract = self._create_hub_contract(node_connections)
        verify_function = hub_contract.get_function_by_name(
            verify_function_name)
        try:
            verify_function(on_chain_request, signature).call().get()
        except web3.exceptions.ContractLogicError as error:
            if _INSUFFICIENT_BALANCE_ERROR in str(error):
                raise self._create_insufficient_balance_error()
            if _INVALID_SIGNATURE_ERROR in str(error):
                raise self._create_invalid_signature_error()
            raise
        nonce = self.__get_nonce(node_connections, internal_transfer_id)
        request = BlockchainClient._TransactionSubmissionStartRequest(
            self._versioned_pantos_hub_abi, function_selector,
            (on_chain_request, signature), gas, None, nonce)
        try:
            return self._start_transaction_submission(request,
                                                      node_connections)
        except (TransactionNonceTooLowError, TransactionUnderpricedError):
            database_access.reset_transfer_nonce(internal_transfer_id)
            raise
