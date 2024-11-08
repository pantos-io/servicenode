import json

from apispec.ext.marshmallow import MarshmallowPlugin
from apispec_webframeworks.flask import FlaskPlugin
from flasgger import APISpec  # type: ignore
from flasgger import Swagger

from pantos.servicenode.restapi import _BidSchema
from pantos.servicenode.restapi import _BidsSchema
from pantos.servicenode.restapi import _TransferSchema
from pantos.servicenode.restapi import _TransferStatusSchema
from pantos.servicenode.restapi import flask_app

plugins = [FlaskPlugin(), MarshmallowPlugin()]
spec = APISpec("Pantos Service Node APISpec", '1.0', "3.0.2", plugins=plugins)

template = spec.to_flasgger(
    flask_app, definitions=[
        _BidSchema, _BidsSchema, _TransferSchema, _TransferStatusSchema
    ])

swagger = Swagger(flask_app, template=template, parse=True)

with flask_app.test_request_context():
    data = swagger.get_apispecs()
    data.pop('definitions')
    data.pop('swagger')
    data['servers'] = [{'url': 'https://sn1.testnet.pantos.io'}]

    with open("openapi.json", "w") as f:
        f.write(json.dumps(data, indent=4))
