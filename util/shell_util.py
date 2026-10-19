"""Execute shell commands and log their captured output."""


def run_command(command: str):
    """Run a command synchronously through the system shell.

    Captures stdout and stderr as text and logs both at debug level. A nonzero
    exit status is returned rather than raised as ``CalledProcessError``.

    :param command: Trusted shell command string; shell syntax is interpreted,
        so callers must not interpolate untrusted input without proper escaping.
    :return: Tuple of the integer exit status and stdout with outer whitespace
        stripped. Stderr is logged but not returned.
    :raises OSError: If the shell process cannot be started.
    :raises UnicodeDecodeError: If captured output cannot be decoded as text.
    """
    import subprocess
    from configuration.logging_configuration import logger as log

    command_result = subprocess.run(command,
                                    capture_output=True,
                                    text=True,
                                    shell=True)
    log.debug(
        f"Command: {command}\nReturn code: {command_result.returncode}\nOutput: {command_result.stdout.strip()}\nError: {command_result.stderr.strip()}")
    return command_result.returncode, command_result.stdout.strip()
