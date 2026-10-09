def run_command(command: str):
    """
    Run a shell command and return the result.
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
