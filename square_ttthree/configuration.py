import json
import os
import sys

from square_commons import ConfigReader
from square_logger import SquareLogger

try:
    config_file_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "data", "config.ini"
    )
    config_sample_file_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "data", "config.sample.ini"
    )
    config_dict = ConfigReader(
        config_file_path, config_sample_file_path
    ).read_configuration()

    # get all vars and typecast
    # ===========================================
    # GENERAL
    MODULE_NAME = config_dict["GENERAL"]["MODULE_NAME"]
    # ===========================================

    # ===========================================
    # ENVIRONMENT
    HOST_IP = config_dict["ENVIRONMENT"]["HOST_IP"]
    HOST_PORT = int(config_dict["ENVIRONMENT"]["HOST_PORT"])
    ALLOW_ORIGINS = json.loads(config_dict["ENVIRONMENT"]["ALLOW_ORIGINS"])
    SSL_CRT_FILE_PATH = config_dict["ENVIRONMENT"]["SSL_CRT_FILE_PATH"]
    SSL_KEY_FILE_PATH = config_dict["ENVIRONMENT"]["SSL_KEY_FILE_PATH"]
    # ===========================================

    # ===========================================
    # DATABASE
    DB_IP = config_dict["DATABASE"]["DB_IP"]
    DB_PORT = int(config_dict["DATABASE"]["DB_PORT"])
    DB_USERNAME = config_dict["DATABASE"]["DB_USERNAME"]
    DB_PASSWORD = config_dict["DATABASE"]["DB_PASSWORD"]
    DB_NAME = config_dict["DATABASE"]["DB_NAME"]
    # ===========================================

    # ===========================================
    # SQUARE_LOGGER
    LOG_FILE_NAME = str(config_dict["SQUARE_LOGGER"]["LOG_FILE_NAME"])
    LOG_LEVEL = int(config_dict["SQUARE_LOGGER"]["LOG_LEVEL"])
    LOG_PATH = config_dict["SQUARE_LOGGER"]["LOG_PATH"]
    LOG_BACKUP_COUNT = int(config_dict["SQUARE_LOGGER"]["LOG_BACKUP_COUNT"])
    FORMATTER_CHOICE = config_dict["SQUARE_LOGGER"]["FORMATTER_CHOICE"]
    ENABLE_REDACTION = (
        config_dict["SQUARE_LOGGER"]["ENABLE_REDACTION"].lower() == "true"
    )
    # ===========================================

except Exception as e:
    print(
        "\033[91mMissing or incorrect config.ini file.\n"
        "Error details: " + str(e) + "\033[0m"
    )
    sys.exit()


DATABASE_URL = (
    f"postgresql+asyncpg://{DB_USERNAME}:{DB_PASSWORD}@{DB_IP}:{DB_PORT}/{DB_NAME}"
)

if FORMATTER_CHOICE not in ("human_readable", "json"):
    raise ValueError(f"Invalid formatter choice: {FORMATTER_CHOICE}")

logger = SquareLogger(
    log_file_name=LOG_FILE_NAME,
    log_level=LOG_LEVEL,
    log_path=LOG_PATH,
    log_backup_count=LOG_BACKUP_COUNT,
    formatter_choice=FORMATTER_CHOICE,
    enable_redaction=ENABLE_REDACTION,
)

# expose logger decorator
auto_logger = logger.auto_logger
