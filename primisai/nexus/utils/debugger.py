import logging, os, json
from datetime import datetime

class Debugger:
    LOG_DIR = 'logs-' + str(datetime.now().strftime("%Y_%m_%d-%H_%M_%S"))

    def __init__(self, name: str, log_level: int = logging.DEBUG):
        self.name = name

        # Ensure the logs directory exists
        if not os.path.exists(self.LOG_DIR):
            os.makedirs(self.LOG_DIR)

        # Set up the logger
        self.logger = logging.getLogger(name)
        self.logger.setLevel(log_level)

        # Create a file handler
        log_file_path = os.path.join(self.LOG_DIR, f"{name}.log")
        file_handler = logging.FileHandler(log_file_path)
        file_handler.setLevel(log_level)

        # Create a formatting configuration
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)

        # Add the file handler to the logger
        self.logger.addHandler(file_handler)

    def log(self, message: str, level: str = "info"):
        level = level.lower()
        if level == "debug":
            self.logger.debug(message)
        elif level == "info":
            self.logger.info(message)
        elif level == "warning":
            self.logger.warning(message)
        elif level == "error":
            self.logger.error(message)
        elif level == "critical":
            self.logger.critical(message)

    def log_dict(self, data: dict, message: str = ""):
        self.logger.info(f"{message}\n{json.dumps(data, indent=2)}")

    def log_list(self, data: list, message: str = ""):
        self.logger.info(f"{message}\n{json.dumps(data, indent=2)}")

    def start_session(self):
        self.logger.info(f"------ New Session Started for {self.name} ------")

    def end_session(self):
        self.logger.info(f"------ Session Ended for {self.name} ------")
