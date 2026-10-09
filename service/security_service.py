from configuration import environment_configuration as env
from configuration.logging_configuration import logger as log
from util import (shell_util,
                  path_util)


def create_crl() -> None:
    log.info("Generating certificate revocation list (CRL)")
    shell_util.run_command(f"""openssl ca \
-config {env.openvpn_pki_path}openssl.cnf \
-gencrl \
-out {env.certificate_revocation_list_path}ca.crl""")


def create_tls_crypt() -> None:
    log.info("Generating TLS crypt key")
    shell_util.run_command(f"""openvpn --genkey secret {env.private_keys_path}ta.key""")
    path_util.assign_permission_to_file(file_path=env.private_keys_path + "ta.key", mode=0o600)
