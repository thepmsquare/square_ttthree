import os
from square_commons import ConfigReader
from square_logger import SquareLogger

# resolve paths relative to this file
_current_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.dirname(_current_dir)

config_file = os.path.join(_project_root, "config.ini")
sample_config = os.path.join(_project_root, "sample.config.ini")

# load configuration using square-commons
config_reader = ConfigReader(file_path=config_file, sample_file_path=sample_config)
config_dict = config_reader.read_configuration()

# expose config keys
DATABASE_URL = config_dict["database"]["DATABASE_URL"]
HOST = config_dict["server"]["HOST"]
PORT = int(config_dict["server"]["PORT"])
SECRET_KEY = config_dict["server"]["SECRET_KEY"]

LOG_LEVEL = int(config_dict["logging"]["LOG_LEVEL"])
LOG_PATH = config_dict["logging"]["LOG_PATH"]

# initialize logger using square-logger
logger = SquareLogger(
    log_file_name="api",
    log_level=LOG_LEVEL,
    log_path=LOG_PATH,
    logger_name="api_logger",
    formatter_choice="human_readable"
)

# expose logger decorator for other api files
auto_logger = logger.auto_logger
