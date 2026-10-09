from configuration import environment_configuration as env
from configuration.logging_configuration import logger as log
from util import path_util
from util import shell_util


def create_ca_private_key() -> None:
    log.info("Creating CA private key")

    shell_util.run_command(f"""openssl genpkey \
-algorithm RSA \
-pkeyopt rsa_keygen_bits:4096 \
-out {env.private_keys_path}ca.key""")
    path_util.assign_permission_to_file(file_path=env.private_keys_path + "ca.key", mode=0o600)


def create_ca_certificate() -> None:
    log.info("Creating CA certificate")

    shell_util.run_command(f"""openssl req \
-config {env.openvpn_pki_path}openssl.cnf \
-key {env.private_keys_path}ca.key \
-new \
-x509 \
-days 3650 \
-sha256 \
-extensions v3_ca \
-out {env.certificates_path}ca.crt""")
