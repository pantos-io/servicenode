import os

import setuptools  # type: ignore

setuptools.setup(
    name='pantos-service-node',
    version=os.getenv('PANTOS_SERVICE_NODE_VERSION', '0.0.0'),
    description='Service node reference implementation for the '
    'Pantos multi-blockchain system',
    packages=setuptools.find_packages(),
    package_data={
        'pantos': [
            'service-node-config.yml', 'service-node-config.env',
            'alembic.ini', 'bids.yml'
        ],
        'pantos.common.blockchains.contracts': ['*.abi'],
        'pantos.servicenode.blockchains.contracts': ['*.abi']
    },
    install_requires=[
        'alembic==1.11.1', 'celery==5.3.1', 'Cerberus==1.3.4', 'Flask==2.3.2',
        'Flask-Cors==4.0.0', 'Flask-RESTful==0.3.10', 'marshmallow==3.19.0',
        'psycopg2-binary==2.9.6', 'PyYAML==6.0.1', 'SQLAlchemy==2.0.18',
        'web3==6.5.0', 'JSON-log-formatter==0.5.2', 'pyaml-env==1.2.1',
        'python-dotenv==1.0.1', 'hexbytes==0.3.1'
    ],
    url='https://github.com/pantos-io/servicenode',
    author='Pantos',
    long_description=('Service node reference implementation for'
                      ' the Pantos multi-blockchain system'),
)
