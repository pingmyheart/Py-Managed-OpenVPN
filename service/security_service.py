"""Generate revocation lists and OpenVPN TLS control-channel key material."""

from configuration import environment_configuration as env
from configuration.logging_configuration import logger as log
from util import (shell_util,
                  path_util)


def create_crl() -> None:
    """Generate ``ca.crl`` from the CA database using ``openssl.cnf``.

    Requests directory mode 0755 and CRL mode 0644 so the unprivileged OpenVPN
    process can read the list. Command and permission failures are not checked.
    """
    log.info("Generating certificate revocation list (CRL)")
    shell_util.run_command(f"""openssl ca \
-config {env.openvpn_pki_path}openssl.cnf \
-gencrl \
-out {env.certificate_revocation_list_path}ca.crl""")
    path_util.assign_permission_to_directory(directory_path=env.certificate_revocation_list_path, mode=0o755)
    path_util.assign_permission_to_file(file_path=env.certificate_revocation_list_path + "ca.crl", mode=0o644)


def create_tls_crypt() -> None:
    """Generate ``ta.key`` with OpenVPN and request private-key mode 0600.

    The shared key protects the control channel through ``tls-crypt``.
    Command and permission failures are not checked.
    """
    log.info("Generating TLS crypt key")
    shell_util.run_command(f"""openvpn --genkey secret {env.private_keys_path}ta.key""")
    path_util.assign_permission_to_file(file_path=env.private_keys_path + "ta.key", mode=0o600)
