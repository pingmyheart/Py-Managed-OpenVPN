class ToolNotInstalledException(Exception):
    def __init__(self, tool_name):
        self.tool_name = tool_name
        self.message = f"{tool_name} is not installed. Please install {tool_name} to proceed."
        super().__init__(self.message)
