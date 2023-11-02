from logging import DEBUG

FOLDER_LOGS = "logs"
LOGGING_LEVEL = DEBUG

class CustomLogger():
    def __init__(self, name):
        import sys
        import logging
        from datetime import datetime
        # Configure the root logger & delete the first logger
        logging.basicConfig(level=logging.DEBUG)
        logging.getLogger().removeHandler(logging.getLogger().handlers[0])

        # Create a logger
        self.logger = logging.getLogger(f"app.{name}")

        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(LOGGING_LEVEL)
        today = datetime.now().strftime("%Y_%m_%d")
        file_handler = logging.FileHandler(f"{FOLDER_LOGS}\\logs_{today}.log", encoding="utf-8")
        file_handler.setLevel(LOGGING_LEVEL)

        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        console_handler.setFormatter(formatter)
        file_handler.setFormatter(formatter)

        self.logger.addHandler(console_handler)
        self.logger.addHandler(file_handler)
