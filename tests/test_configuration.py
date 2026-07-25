import importlib
from unittest.mock import MagicMock, patch

import pytest

import square_ttthree.configuration


@pytest.fixture
def mock_config_dict():
    return {
        "GENERAL": {"MODULE_NAME": "square_ttthree"},
        "ENVIRONMENT": {
            "HOST_IP": "0.0.0.0",
            "HOST_PORT": "8000",
            "ALLOW_ORIGINS": '["*"]',
            "SSL_CRT_FILE_PATH": "",
            "SSL_KEY_FILE_PATH": "",
        },
        "SQUARE_LOGGER": {
            "LOG_FILE_NAME": "square_ttthree.log",
            "LOG_LEVEL": "10",
            "LOG_PATH": "logs",
            "LOG_BACKUP_COUNT": "5",
            "FORMATTER_CHOICE": "human_readable",
            "ENABLE_REDACTION": "true",
        },
    }


def test_configuration_exception(get_patched_configuration, mock_config_dict, capsys):
    invalid_dict = mock_config_dict.copy()
    invalid_dict["ENVIRONMENT"] = invalid_dict["ENVIRONMENT"].copy()
    invalid_dict["ENVIRONMENT"]["HOST_PORT"] = "not_an_int"

    mock_instance = MagicMock()
    mock_instance.read_configuration.return_value = invalid_dict

    with patch("square_commons.ConfigReader", return_value=mock_instance):
        with pytest.raises(SystemExit):
            importlib.reload(square_ttthree.configuration)

    captured = capsys.readouterr()
    assert "Missing or incorrect config.ini file." in captured.out
    assert "invalid literal for int()" in captured.out

    # restore configuration
    importlib.reload(square_ttthree.configuration)


def test_configuration_invalid_formatter(get_patched_configuration, mock_config_dict):
    invalid_dict = mock_config_dict.copy()
    invalid_dict["SQUARE_LOGGER"] = invalid_dict["SQUARE_LOGGER"].copy()
    invalid_dict["SQUARE_LOGGER"]["FORMATTER_CHOICE"] = "invalid_formatter"

    mock_instance = MagicMock()
    mock_instance.read_configuration.return_value = invalid_dict

    with patch("square_commons.ConfigReader", return_value=mock_instance):
        with pytest.raises(
            ValueError, match="Invalid formatter choice: invalid_formatter"
        ):
            importlib.reload(square_ttthree.configuration)

    # restore configuration
    importlib.reload(square_ttthree.configuration)
