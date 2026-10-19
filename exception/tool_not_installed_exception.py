"""Define the exception used when a required external tool is unavailable."""


class ToolNotInstalledException(Exception):
    """Report a missing tool or a failed tool availability check.

    :ivar tool_name: Name of the required executable.
    :ivar message: Installation guidance included in the exception message.
    """

    def __init__(self, tool_name):
        """Create an availability error for a required executable.

        :param tool_name: Display name of the tool that failed its check.
        """
        self.tool_name = tool_name
        self.message = f"{tool_name} is not installed. Please install {tool_name} to proceed."
        super().__init__(self.message)
