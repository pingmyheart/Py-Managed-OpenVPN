"""Filesystem helpers with boolean results for creation and permission changes."""


def check_if_file_exists(file_path: str) -> bool:
    """
    Check whether a path resolves to an existing regular file.

    :param file_path: The path to the file to check.
    :return: ``True`` for a regular file (including a symlink to one), otherwise
        ``False``.
    """
    import os

    return os.path.isfile(file_path)


def check_if_directory_exists(directory: str) -> bool:
    """
    Check whether a path exists, without requiring it to be a directory.

    :param directory: The path to the directory to check.
    :return: ``True`` if the path exists, including when it is a regular file.
    """
    import os

    return os.path.exists(directory)


def secure_create_path_for_file(file_path: str) -> bool:
    """
    Create the parent directory of a file path with requested mode 0700.

    Existing permissions are left unchanged. ``os.makedirs`` applies the mode
    to the leaf directory; intermediate directories use its standard defaults.

    :param file_path: The path to the file for which to create the directory.
    :return: ``True`` if the parent path exists or was created, ``False`` if
        directory creation raises ``OSError``.
    """
    import os

    directory = os.path.dirname(file_path)
    if not os.path.exists(directory):
        try:
            os.makedirs(directory, mode=0o700, exist_ok=True)
        except OSError:
            return False
    return True


def secure_create_file(file_path: str, data: str) -> bool:
    """
    Write text to a file, then set its permission mode to 0600.

    Creates missing parent directories through ``secure_create_path_for_file``.
    Existing files are truncated. Permissions are changed after writing, so this
    is not an atomic secure-creation operation.

    :param file_path: The path to the file to create.
    :param data: The data to write to the file.
    :return: ``True`` if writing and chmod succeed, ``False`` if parent creation
        fails or an ``OSError`` occurs. A failure may leave a modified file.
    :raises UnicodeEncodeError: If the data cannot be encoded using the default
        text encoding.
    """
    import os

    if secure_create_path_for_file(file_path):
        try:
            with open(file_path, 'w') as file:
                file.write(data)
            os.chmod(file_path, 0o600)
            return True
        except OSError:
            return False
    return False


def assign_permission_to_directory(directory_path: str, mode) -> bool:
    """
    Assign the specified permission mode to a directory at the given path.

    The existence check does not verify that the path is a directory.

    :param directory_path: Path whose permissions should be changed.
    :param mode: Integer permission bits, for example ``0o700``.
    :return: ``True`` if chmod succeeds; ``False`` if the path is absent or
        chmod raises ``OSError``.
    """
    import os

    if check_if_directory_exists(directory_path):
        try:
            os.chmod(directory_path, mode)
            return True
        except OSError:
            return False
    return False


def assign_permission_to_file(file_path: str, mode) -> bool:
    """
    Assign the specified permission mode to a file at the given path.

    :param file_path: The path to the file.
    :param mode: Integer permission bits, for example ``0o600``.
    :return: ``True`` if chmod succeeds; ``False`` if the path is not an existing
        regular file or chmod raises ``OSError``.
    """
    import os

    if check_if_file_exists(file_path):
        try:
            os.chmod(file_path, mode)
            return True
        except OSError:
            return False
    return False


def read_file(file_path: str):
    """
    Read the contents of a file at the given path.

    :param file_path: The path to the file to read.
    :return: The complete contents as text using the default encoding.
    :raises OSError: If the file cannot be opened or read.
    :raises UnicodeDecodeError: If the contents cannot be decoded as text.
    """
    return open(file_path, 'r').read()


def delete_file(file_path: str):
    """
    Delete a file at the given path if it exists.

    :param file_path: The path to the file to delete.
    :return: ``True`` if removed, ``False`` if the path is not a regular file.
    :raises OSError: If a file passes the existence check but removal fails.
    """
    import os
    if check_if_file_exists(file_path):
        os.remove(file_path)
        return True
    return False
