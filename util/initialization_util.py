from configuration.environment_configuration import private_keys_path, certificates_path, \
    certificate_revocation_list_path, certificate_sign_request_path, new_certificates_path, openvpn_pki_path, \
    openvpn_conf_path, openvpn_log_path, openvpn_rules_path
from configuration.logging_configuration import logger as log
from service import (get_certificate_expiration_in_epoch_millis,
                     actual_timestamp_in_millis,
                     get_crl_expiration_in_epoch_millis)
from util import (path_util,
                  openssl_util)

need_to_restart = False


def initialize_path():
    for _, required_path in enumerate([private_keys_path,
                                       openvpn_conf_path,
                                       openvpn_log_path,
                                       openvpn_rules_path,
                                       certificates_path,
                                       new_certificates_path,
                                       certificate_revocation_list_path,
                                       certificate_sign_request_path]):
        if not path_util.check_if_directory_exists(required_path):
            log.info(f"Required path '{required_path}' does not exist. Creating it.")
            path_util.secure_create_path_for_file(required_path)
        else:
            log.info(f"Required path '{required_path}' already exists. Skipping creation.")


def initialize_pki_files():
    log.info("Initializing OpenVPN PKI")

    path_util.secure_create_file(file_path=openvpn_pki_path + "index.txt",
                                 data="") if path_util.check_if_file_exists(
        openvpn_pki_path + "index.txt") is False else None
    path_util.secure_create_file(file_path=openvpn_pki_path + "serial",
                                 data="1000") if path_util.check_if_file_exists(
        openvpn_pki_path + "serial") is False else None
    path_util.secure_create_file(file_path=openvpn_pki_path + "crlnumber",
                                 data="1000") if path_util.check_if_file_exists(
        openvpn_pki_path + "crlnumber") is False else None


def initialize_openssl_configuration():
    openssl_util.create_openssl_conf_file()


def initialize_certification_authority():
    global need_to_restart
    # Generate or renew CA
    if not path_util.check_if_file_exists(private_keys_path + "ca.key"):
        from service.ca_service import create_ca_private_key
        log.info("CA private key does not exist. Creating it.")
        create_ca_private_key()
    else:
        log.info("CA private key already exists. Skipping creation.")
    if not path_util.check_if_file_exists(certificates_path + "ca.crt"):
        from service.ca_service import create_ca_certificate
        log.info("CA certificate does not exist. Creating it.")
        create_ca_certificate()
    else:
        log.info("CA certificate already exists. Skipping creation.")
    if ((get_certificate_expiration_in_epoch_millis(certificates_path + "ca.crt") - actual_timestamp_in_millis())
            < 30 * 24 * 60 * 60 * 1000):
        from service.ca_service import create_ca_certificate
        log.info("CA certificate is expiring soon. Renewing it.")
        create_ca_certificate()
        need_to_restart = True


def initialize_server():
    global need_to_restart
    # Generate or renew server
    if not path_util.check_if_file_exists(private_keys_path + "server.key"):
        from service.server_service import create_server_private_key
        log.info("Server private key does not exist. Creating it.")
        create_server_private_key()
    else:
        log.info("Server private key already exists. Skipping creation.")
    if not path_util.check_if_file_exists(certificates_path + "server.crt"):
        from service.server_service import create_server_certificate
        log.info("Server certificate does not exist. Creating it.")
        create_server_certificate()
    else:
        log.info("Server certificate already exists. Skipping creation.")
    if ((get_certificate_expiration_in_epoch_millis(certificates_path + "server.crt") - actual_timestamp_in_millis())
            < 30 * 24 * 60 * 60 * 1000):
        from service.server_service import create_server_certificate
        log.info("Server certificate is expiring soon. Renewing it.")
        create_server_certificate()
        need_to_restart = True
    else:
        log.info("Server certificate is valid. Skipping renewal.")


def initialize_crl():
    global need_to_restart
    # Generate or renew crl
    if not path_util.check_if_file_exists(certificate_revocation_list_path + "ca.crl"):
        from service.security_service import create_crl
        log.info("CRL does not exist. Creating it.")
        create_crl()
    else:
        log.info("CRL already exists. Skipping creation.")
    if ((get_crl_expiration_in_epoch_millis(certificate_revocation_list_path + "ca.crl") - actual_timestamp_in_millis())
            < 5 * 24 * 60 * 60 * 1000):
        from service.security_service import create_crl
        log.info("CRL is expiring soon. Renewing it.")
        create_crl()
        need_to_restart = True
    else:
        log.info("CRL is valid. Skipping renewal.")


def initialize_tls_key():
    # Generate tls key
    if not path_util.check_if_file_exists(private_keys_path + "ta.key"):
        from service.security_service import create_tls_crypt
        log.info("TLS crypt key does not exist. Creating it.")
        create_tls_crypt()
    else:
        log.info("TLS crypt key already exists. Skipping creation.")


def initialize_openvpn_files():
    # Generate openvpn configuration
    from service.openvpn_service import create_openvpn_configuration
    from configuration.environment_configuration import openvpn_server_network_mode
    create_openvpn_configuration(openvpn_server_network_mode)


def initialize_need_to_restart_file():
    # Generate need to restart file
    from service.openvpn_service import create_need_to_restart_file
    create_need_to_restart_file()


def initialize_iptables_rules():
    # Generate iptables rules file
    from service import iptables_service
    iptables_service.generate_create_rules_file()
    iptables_service.generate_delete_rules_file()


def initialize():
    initialize_path()
    initialize_pki_files()
    initialize_openssl_configuration()
    initialize_certification_authority()
    initialize_server()
    initialize_crl()
    initialize_tls_key()
    initialize_openvpn_files()
    initialize_need_to_restart_file()
    initialize_iptables_rules()


def refresh():
    global need_to_restart
    need_to_restart = False
    initialize_certification_authority()
    initialize_server()
    initialize_crl()
    if need_to_restart:
        initialize_need_to_restart_file()
    need_to_restart = False
