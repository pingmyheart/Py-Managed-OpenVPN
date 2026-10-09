def check_if_file_exists(file_path: str) -> bool:
    """
    Check if a file exists at the given path.
    :param file_path: The path to the file to check.
    :return: True if the file exists, False otherwise.
    """
    import os

    return os.path.isfile(file_path)


def check_if_directory_exists(directory: str) -> bool:
    """
    Check if a directory exists at the given path.
    :param directory: The path to the directory to check.
    :return: True if the directory exists, False otherwise.
    """
    import os

    return os.path.exists(directory)


def secure_create_path_for_file(file_path: str) -> bool:
    """
    Create the directory path for a given file path with secure permissions (700).
    :param file_path: The path to the file for which to create the directory.
    :return: True if the directory was created or already exists, False otherwise.
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
        Create a file at the given path with secure permissions (600) and write the provided data to it.
    :param file_path: The path to the file to create.
    :param data: The data to write to the file.
    :return: True if the file was created and written to successfully, False otherwise.
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
    :param directory: The path to the directory.
    :param mode: The permission mode to assign.
    :return: True if the permission was successfully assigned, False otherwise.
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
    :param mode: The permission mode to assign.
    :return: True if the permission was successfully assigned, False otherwise.
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
    :return: The contents of the file.
    """
    return open(file_path, 'r').read()


def delete_file(file_path: str):
    """
    Delete a file at the given path if it exists.
    :param file_path: The path to the file to delete.
    :return: True if the file was deleted, False otherwise.
    """
    import os
    if check_if_file_exists(file_path):
        os.remove(file_path)
        return True
    return False
