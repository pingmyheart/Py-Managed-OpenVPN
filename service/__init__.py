"""Read PEM certificate metadata and provide timestamp helpers."""


def get_certificate_expiration_in_epoch_millis(certificate_path: str) -> int:
    """Read a PEM certificate's expiration time in milliseconds.

    The UTC date components are converted with ``time.mktime``, which interprets
    them in the process's local timezone. The result matches the UTC epoch
    timestamp only when that timezone is UTC.

    :param certificate_path: Path to the PEM-encoded certificate.
    :return: Expiration time converted to milliseconds using the local timezone.
    :raises OSError: If the certificate cannot be read.
    :raises ValueError: If the certificate data cannot be parsed.
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
    """Read a PEM revocation list's next-update time in milliseconds.

    As with certificate expiration, ``time.mktime`` interprets the UTC date
    components in the process's local timezone.

    :param crl_path: Path to the PEM-encoded certificate revocation list.
    :return: Next-update time converted to milliseconds using the local timezone.
    :raises OSError: If the CRL cannot be read.
    :raises ValueError: If the CRL data cannot be parsed.
    :raises AttributeError: If the CRL has no next-update date.
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

    :return: Integer milliseconds since the Unix epoch, truncated from the
        system wall-clock time.
    """
    import time

    return int(time.time() * 1000)


def extract_subjects_from_certificate(certificate_path: str):
    """Extract the subject from a PEM-encoded X.509 certificate.

    :param certificate_path: Path to the PEM certificate to read.
    :return: A ``cryptography.x509.Name`` containing the subject attributes.
    :raises OSError: If the certificate cannot be read.
    :raises ValueError: If the certificate data cannot be parsed.
    """
    from cryptography import x509
    from cryptography.hazmat.backends import default_backend

    with open(certificate_path, "rb") as cert_file:
        cert_data = cert_file.read()
        cert = x509.load_pem_x509_certificate(cert_data, default_backend())
        subjects = cert.subject
        return subjects
