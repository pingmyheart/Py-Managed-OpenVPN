def get_certificate_expiration_in_epoch_millis(certificate_path: str) -> int:
    """
        Obtain the certificate expiration date in epoch milliseconds using cryptography library.
    :param certificate_path: The path to the certificate file.
    :return: The expiration date in epoch milliseconds.
    """
    from cryptography import x509
    from cryptography.hazmat.backends import default_backend
    import time

    with open(certificate_path, "rb") as cert_file:
        cert_data = cert_file.read()
        cert = x509.load_pem_x509_certificate(cert_data, default_backend())
        expiration_date = cert.not_valid_after_utc
        epoch_millis = int(time.mktime(expiration_date.timetuple()) * 1000)
        return epoch_millis


def get_crl_expiration_in_epoch_millis(crl_path: str) -> int:
    """
        Obtain the CRL expiration date in epoch milliseconds using cryptography library.
    :param crl_path: The path to the CRL file.
    :return: The expiration date in epoch milliseconds.
    """
    from cryptography import x509
    from cryptography.hazmat.backends import default_backend
    import time

    with open(crl_path, "rb") as crl_file:
        crl_data = crl_file.read()
        crl = x509.load_pem_x509_crl(crl_data, default_backend())
        expiration_date = crl.next_update_utc
        epoch_millis = int(time.mktime(expiration_date.timetuple()) * 1000)
        return epoch_millis


def actual_timestamp_in_millis() -> int:
    """
    Get the current timestamp in epoch milliseconds.
    :return: The current timestamp in epoch milliseconds.
    """
    import time

    return int(time.time() * 1000)


def extract_subjects_from_certificate(certificate_path: str):
    """
        Extract the subject components from a certificate using the cryptography library.
    :param certificate_path: Path to certificate
    :return: subjects
    """
    from cryptography import x509
    from cryptography.hazmat.backends import default_backend

    with open(certificate_path, "rb") as cert_file:
        cert_data = cert_file.read()
        cert = x509.load_pem_x509_certificate(cert_data, default_backend())
        subjects = cert.subject
        return subjects
