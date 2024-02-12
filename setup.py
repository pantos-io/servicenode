import os

import setuptools

setuptools.setup(
    name='pantos-service-node',
    version=os.getenv('PANTOS_SERVICE_NODE_VERSION'),
    description='Service node reference implementation for the '
    'Pantos multi-blockchain system', packages=setuptools.find_packages(),
    package_data={
        'pantos': ['pantos-service-node.conf', 'alembic.ini', 'bids.yaml'],
        'pantos.common.blockchains.contracts': ['*.abi'],
        'pantos.servicenode.blockchains.contracts': ['*.abi']
    }, install_requires=[
        'alembic==1.11.1', 'celery==5.3.1', 'Cerberus==1.3.4', 'Flask==2.3.2',
        'Flask-Cors==4.0.0', 'Flask-RESTful==0.3.10', 'marshmallow==3.19.0',
        'psycopg2==2.9.6', 'PyYAML==6.0.1', 'SQLAlchemy==2.0.18', 'web3==6.5.0',
        'JSON-log-formatter==0.5.2'
    ],
    url='https://github.com/pantos-io/servicenode',
    author='Pantos',
    long_description='Service node reference implementation for the Pantos multi-blockchain system',
)
