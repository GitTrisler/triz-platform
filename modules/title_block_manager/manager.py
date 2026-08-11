class TitleBlockManager:
    def __init__(self, platform=None):
        self.platform = platform

    def write(self, message, level="INFO"):
        if self.platform:
            self.platform.output_write(message, level)
        else:
            print(f"[{level}] {message}")

    def scan(self):
        self.write("Scan requested.", "INFO")

    def run(self):
        self.write("Update requested.", "INFO")