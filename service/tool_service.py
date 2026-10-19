"""Check external tool availability by executing their version commands."""


def check_openvpn_is_installed():
    """
    Check whether the OpenVPN version command can run successfully.

    :return: ``True`` if ``openvpn --version`` exits successfully; ``False`` if
        the executable is missing or exits with a nonzero status.
    :raises OSError: For process launch failures other than a missing executable.
    """
    import subprocess

    try:
        subprocess.run(["openvpn", "--version"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def check_openssl_is_installed():
    """
    Check whether the OpenSSL version command can run successfully.

    :return: ``True`` if ``openssl version`` exits successfully; ``False`` if
        the executable is missing or exits with a nonzero status.
    :raises OSError: For process launch failures other than a missing executable.
    """
    import subprocess

    try:
        subprocess.run(["openssl", "version"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False
