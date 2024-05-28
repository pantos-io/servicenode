#! /usr/bin/env python3
# Source: https://github.com/pantos-io/common/blob/main/scripts/generate-signer-key.py
"""Generate a private key to be used with the pantos.common.signer
module.

"""
import getpass
import random
import string

import Crypto.PublicKey.ECC

passphrase = getpass.getpass('Passphrase: ')
random_string = ''.join(
    random.choices(string.ascii_lowercase + string.digits, k=8))
key_file_name = f'signer-key-{random_string}.pem'
key = Crypto.PublicKey.ECC.generate(curve='Ed25519')

with open(key_file_name, 'wt') as key_file:
    key_file.write(
        key.export_key(format='PEM', passphrase=passphrase,
                       protection='PBKDF2WithHMAC-SHA1AndAES128-CBC'))

print(f'PEM file written to {key_file_name}')