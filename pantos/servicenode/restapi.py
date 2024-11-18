"""Module that implements the service node's REST API.

"""
import logging
import time
import typing
import uuid

import flask
import flask_cors  # type: ignore
import flask_restful  # type: ignore
import flask_restful.reqparse  # type: ignore
import marshmallow
import marshmallow.validate
from pantos.common.blockchains.enums import Blockchain
from pantos.common.entities import ServiceNodeBid
from pantos.common.restapi import Live
from pantos.common.restapi import NodesHealthResource
from pantos.common.restapi import bad_request
from pantos.common.restapi import conflict
from pantos.common.restapi import internal_server_error
from pantos.common.restapi import not_acceptable
from pantos.common.restapi import ok_response
from pantos.common.restapi import resource_not_found

from pantos.servicenode.blockchains.factory import get_blockchain_client
from pantos.servicenode.business.bids import BidInteractor
from pantos.servicenode.business.transfers import SenderNonceNotUniqueError
from pantos.servicenode.business.transfers import TransferInteractor
from pantos.servicenode.business.transfers import \
    TransferInteractorBidNotAcceptedError
from pantos.servicenode.business.transfers import \
    TransferInteractorResourceNotFoundError
from pantos.servicenode.configuration import get_blockchain_config

flask_app = flask.Flask(__name__)
"""Flask application object."""

# Allow CORS for all domains on all routes
flask_cors.CORS(flask_app)

_logger = logging.getLogger(__name__)
"""Logger for this module."""


class _BidSchema(marshmallow.Schema):
    """Validation schema for a bid within a transfer request.

    """
    execution_time = marshmallow.fields.Integer(required=True)
    valid_until = marshmallow.fields.Integer(required=True)
    fee = marshmallow.fields.Integer(required=True)
    signature = marshmallow.fields.String(required=True)


class _TransferSchema(marshmallow.Schema):
    """Validation schema for the transfer endpoint parameters.

    """
    source_blockchain_id = marshmallow.fields.Integer(required=True)
    destination_blockchain_id = marshmallow.fields.Integer(
        required=True, validate=marshmallow.validate.OneOf(
            [blockchain.value for blockchain in Blockchain]))
    sender_address = marshmallow.fields.String(required=True)
    recipient_address = marshmallow.fields.String(required=True)
    source_token_address = marshmallow.fields.String(required=True)
    destination_token_address = marshmallow.fields.String(required=True)
    valid_until = marshmallow.fields.Integer(required=True)
    amount = marshmallow.fields.Integer(required=True)
    nonce = marshmallow.fields.Integer(required=True)
    signature = marshmallow.fields.String(required=True)
    bid = marshmallow.fields.Nested(_BidSchema, required=True)
    time_received = marshmallow.fields.Integer(required=True)

    @marshmallow.validates("source_blockchain_id")
    def __validate_source_blockchain_id(self, blockchain_id: int) -> None:
        supported_blockchains_ids = [
            blockchain.value for blockchain in Blockchain
        ]
        if blockchain_id not in supported_blockchains_ids:
            raise marshmallow.ValidationError(
                message='This is not a supported blockchain. '
                f'Must be one of: {supported_blockchains_ids}.',
                field_name='source_blockchain_id')
        blockchain_config = get_blockchain_config(Blockchain(blockchain_id))
        active = blockchain_config['active']
        registered = blockchain_config['registered']
        if not active or not registered:
            raise marshmallow.ValidationError(
                message='This is not an active blockchain.',
                field_name='source_blockchain_id')

    @marshmallow.validates_schema
    def __validate_schema(self, data: typing.Dict[str, typing.Any],
                          **kwargs) -> None:
        # Check the arguments without any expensive computations or
        # network communications (more expensive checks are only
        # performed asynchronously)
        source_blockchain = Blockchain(data['source_blockchain_id'])
        destination_blockchain = Blockchain(data['destination_blockchain_id'])

        self.__check_valid_sender_address(source_blockchain,
                                          data['sender_address'])
        self.__check_valid_recipient_address(destination_blockchain,
                                             data['recipient_address'])
        self.__check_valid_source_token_address(source_blockchain,
                                                data['source_token_address'])
        self.__check_valid_destination_token_address(
            destination_blockchain, data['destination_token_address'])
        self.__check_amount(data['amount'])

    def __check_valid_sender_address(self, source_blockchain: Blockchain,
                                     sender_address: str) -> None:
        if not get_blockchain_client(source_blockchain).is_valid_address(
                sender_address):
            _logger.warning('new transfer request: invalid sender address '
                            f'"{sender_address}"')
            raise marshmallow.ValidationError(
                message='sender address must be a valid blockchain '
                f'address on {source_blockchain.name}',
                field_name='sender_address')

    def __check_valid_recipient_address(self,
                                        destination_blockchain: Blockchain,
                                        recipient_address: str) -> None:
        if not get_blockchain_client(
                destination_blockchain).is_valid_recipient_address(
                    recipient_address):
            _logger.warning(
                'new transfer request: invalid recipient address', extra={
                    'recipient_address': recipient_address,
                    'destination_blockchain': destination_blockchain.name
                })
            raise marshmallow.ValidationError(
                'recipient address must be a valid blockchain '
                'address, different from the 0 address on '
                f'{destination_blockchain.name}',
                field_name='recipient_address')

    def __check_valid_source_token_address(self, source_blockchain: Blockchain,
                                           source_token_address: str) -> None:
        if not get_blockchain_client(source_blockchain).is_valid_address(
                source_token_address):
            _logger.warning('new transfer request: invalid source token '
                            f'address "{source_token_address}"')
            raise marshmallow.ValidationError(
                message='source token address must be a valid blockchain '
                f'address on {source_blockchain.name}',
                field_name='source_token_address')

    def __check_valid_destination_token_address(
            self, destination_blockchain: Blockchain,
            destination_token_address: str) -> None:
        if not get_blockchain_client(destination_blockchain).is_valid_address(
                destination_token_address):
            _logger.warning('new transfer request: invalid destination token '
                            f'address "{destination_token_address}"')
            raise marshmallow.ValidationError(
                message='destination token address must be a valid '
                f'blockchain address on {destination_blockchain.name}',
                field_name='destination_token_address')

    def __check_amount(self, amount: int) -> None:
        if amount <= 0:
            _logger.warning(
                'new transfer request: invalid amount {}'.format(amount))
            raise marshmallow.ValidationError(
                message='amount must be greater than 0', field_name='amount')

    @marshmallow.post_load
    def make_initiate_transfer_request(
            self, data: typing.Dict[str, typing.Any],
            **kwargs) -> TransferInteractor.InitiateTransferRequest:
        data['source_blockchain'] = Blockchain(
            data.pop('source_blockchain_id'))
        data['destination_blockchain'] = Blockchain(
            data.pop('destination_blockchain_id'))

        data['bid'] = ServiceNodeBid(data['source_blockchain'],
                                     data['destination_blockchain'],
                                     data['bid']['fee'],
                                     data['bid']['execution_time'],
                                     data['bid']['valid_until'],
                                     data['bid']['signature'])

        return TransferInteractor.InitiateTransferRequest(**data)


class _TransferStatusSchema(marshmallow.Schema):
    """Validation schema for the transfer status endpoint parameters.

    """
    task_id = marshmallow.fields.UUID(required=True)

    @marshmallow.post_load
    def make_task_id(self, data: typing.Dict[str, typing.Any],
                     **kwargs) -> uuid.UUID:
        return data['task_id']


class _BidsSchema(marshmallow.Schema):
    """Validation schema for the bids endpoint parameters.

    """
    source_blockchain = marshmallow.fields.Integer(
        required=True, validate=marshmallow.validate.OneOf(
            [blockchain.value for blockchain in Blockchain]))
    destination_blockchain = marshmallow.fields.Integer(
        required=True, validate=marshmallow.validate.OneOf(
            [blockchain.value for blockchain in Blockchain]))


class _Transfer(flask_restful.Resource):
    """RESTful resource for token transfer requests.

    """
    def post(self) -> flask.Response:
        """
        Endpoint for submitting a token transfer request.
        ---
        tags:
          - Transfer
        requestBody:
          description: Transfer request
          required: true
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/_Transfer"
        responses:
            200:
              description: Transfer request accepted
              content:
                application/json:
                  schema:
                    type: object
                    properties:
                      task_id:
                        type: string
            406:
              description: Transfer request no accepted
              content:
                application/json:
                  schema:
                    type: array
                    items:
                      type: string
                    example: "[bid has been rejected by service node: \
'bid not accepted']"
            409:
              description: Sender nonce from transfer request is not unique
              content:
                application/json:
                  schema:
                    type: string
                    example: sender nonce 1337 is not unique
            500:
              description: Internal server error
        """
        try:
            time_received = time.time()
            arguments = flask_restful.request.json
            initiate_transfer_request = _TransferSchema().load(
                arguments | {'time_received': time_received})
            _logger.info('new transfer request', extra=arguments)
            task_id = TransferInteractor().initiate_transfer(
                initiate_transfer_request)
        except marshmallow.ValidationError as error:
            not_acceptable(error.messages)
        except SenderNonceNotUniqueError as error:
            _logger.warning(f'new transfer request: {error}')
            conflict('sender nonce '
                     f'{initiate_transfer_request.nonce} is not unique')
        except TransferInteractorBidNotAcceptedError as error:
            _logger.warning(f'bid has been rejected by service node: {error}')
            not_acceptable([f'bid has been rejected by service node: {error}'])
        except Exception:
            _logger.critical('unable to process a transfer request',
                             exc_info=True)
            internal_server_error()
        return ok_response({'task_id': str(task_id)})


class _TransferStatus(flask_restful.Resource):
    """RESTful resource for token transfer status requests.

    """
    def get(self, task_id: str) -> flask.Response:
        """
        Endpoint that returns the status of a transfer.
        ---
        tags:
          - Transfer Status
        parameters:
          - in: path
            name: task_id
            schema:
              $ref: '#/components/schemas/_TransferStatus'
            required: true
            description: Id of a transfer submitted to the service node
        responses:
          200:
            description: Object containing the status of a transfer with
             the given task ID
            content:
              application/json:
                schema:
                  type: object
                  properties:
                    task_id:
                      type: string
                    source_blockchain_id:
                      $ref: "#/components/schemas/\
_Bids/properties/source_blockchain"
                    destination_blockchain_id:
                      $ref: "#/components/schemas/\
_Bids/properties/destination_blockchain"
                    sender_address:
                      type: string
                    recipient_address:
                      type: string
                    source_token_address:
                      type: string
                    destination_token_address:
                      type: string
                    amount:
                      type: integer
                    fee:
                      type: integer
                    status:
                      type: string
                    transfer_id:
                      type: string
                    transaction_id:
                      type: string
          404:
            description: 'not found'
            content:
              application/json:
                schema:
                  type: string
                  example: {"message": "task ID 123 is unknown"}
          500:
            description: 'internal server error'
        """
        try:
            task_id_uuid = _TransferStatusSchema().load({'task_id': task_id})
            _logger.info(f'new transfer status request: {task_id}')
            find_transfer_response = TransferInteractor().find_transfer(
                task_id_uuid)
        except marshmallow.ValidationError:
            _logger.warning('new transfer status request: task ID '
                            f'"{task_id}" is not a UUID')
            resource_not_found(f'task ID {task_id} is not a UUID')
        except TransferInteractorResourceNotFoundError:
            _logger.warning('new transfer status request: unknown task ID '
                            f'"{task_id}"')
            resource_not_found(f'task ID {task_id} is unknown')
        except Exception:
            _logger.critical('unable to process a transfer status request',
                             exc_info=True)
            internal_server_error()
        return ok_response({
            'task_id': str(task_id_uuid),
            'source_blockchain_id': find_transfer_response.source_blockchain.
            value,
            'destination_blockchain_id': find_transfer_response.
            destination_blockchain.value,
            'sender_address': find_transfer_response.sender_address,
            'recipient_address': find_transfer_response.recipient_address,
            'source_token_address': find_transfer_response.
            source_token_address,
            'destination_token_address': find_transfer_response.
            destination_token_address,
            'amount': find_transfer_response.amount,
            'fee': find_transfer_response.fee,
            'status': find_transfer_response.status.to_public_status().name.
            lower(),
            'transfer_id': '' if find_transfer_response.transfer_id is None
            else find_transfer_response.transfer_id,
            'transaction_id': '' if find_transfer_response.transaction_id
            is None else find_transfer_response.transaction_id
        })


class _Bids(flask_restful.Resource):
    """RESTful resource for token transfer bids.

    """
    def get(self) -> flask.Response:
        """
        Endpoint that returns a list of bids for a given source and \
destination blockchain.
        ---
        tags:
          - Bids
        parameters:
          - in: query
            name: source_blockchain
            schema:
              $ref: '#/components/schemas/_Bids/properties/source_blockchain'
            required: true
            description: Numeric ID of the supported Blockchain ID
          - in: query
            name: destination_blockchain
            schema:
              $ref: \
                '#/components/schemas/_Bids/properties/destination_blockchain'
            required: true
            description: Numeric ID of the supported Blockchain ID
        responses:
          200:
            description: List of bids for a given source and \
destination blockchain
            content:
              application/json:
                schema:
                  $ref: '#/components/schemas/_Bid'
          400:
            description: 'bad request'
            content:
              application/json:
                schema:
                  type: string
                  example: {"message": {"source_blockchain": \
                    ["Missing data for required field."], \
                    "destination_blockchain": \
                    ["Missing data for required field."]}}
          500:
            description: 'internal server error'
        """
        try:
            query_arguments = flask_restful.request.args
            bids_parameter = _BidsSchema().load(query_arguments)
            _logger.info('new bids request', extra=bids_parameter)
            bids = BidInteractor().get_current_bids(
                bids_parameter['source_blockchain'],
                bids_parameter['destination_blockchain'])
        except marshmallow.ValidationError as ve:
            _logger.warning(f"new bids request: {ve.messages}")
            bad_request(ve.messages)
        except Exception:
            _logger.critical('unable to process a bids request', exc_info=True)
            internal_server_error()

        return ok_response(bids)


# Register the RESTful resources
_restful_api = flask_restful.Api(flask_app)
_restful_api.add_resource(Live, '/health/live')
_restful_api.add_resource(NodesHealthResource, '/health/nodes')
_restful_api.add_resource(_Transfer, '/transfer')
_restful_api.add_resource(_TransferStatus, '/transfer/<string:task_id>/status')
_restful_api.add_resource(_Bids, '/bids')
