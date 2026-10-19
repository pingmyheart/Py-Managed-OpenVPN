"""Generate the certification authority's private key and self-signed certificate."""

from configuration import environment_configuration as env
from configuration.logging_configuration import logger as log
from util import path_util
from util import shell_util


def create_ca_private_key() -> None:
    """Generate ``ca.key`` as a 4096-bit RSA key and request mode 0600.

    Uses the configured private-key directory. Command exit codes and permission
    helper failures are not checked by this function.
    """
    log.info("Creating CA private key")

    shell_util.run_command(f"""openssl genpkey \
-algorithm RSA \
-pkeyopt rsa_keygen_bits:4096 \
-out {env.private_keys_path}ca.key""")
    path_util.assign_permission_to_file(file_path=env.private_keys_path + "ca.key", mode=0o600)


def create_ca_certificate() -> None:
    """Issue a self-signed CA certificate valid for 3650 days using SHA-256.

    Requires the existing CA key and ``openssl.cnf`` with the ``v3_ca``
    extension and configured CA subject. Writes ``ca.crt`` to the certificate
    directory without checking the OpenSSL exit code.
    """
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
