"""
Centralized configuration management for WaifuAPI.
"""
import os
from typing import Dict, Any, Optional
from dataclasses import dataclass
from .waifuapi_logging import get_logger

logger = get_logger("config")


@dataclass
class WaifuAPIConfig:
    """Configuration class for WaifuAPI."""

    # Database configuration
    database_file: str = "dialogs.db"

    # AI Model configuration
    model_url: str = "http://localhost:80/path/"
    default_response: str = "The AI model is currently unavailable. Please try again later."
    default_genre: str = "Romance"

    # Translation configuration
    translation_service: str = "google"  # google, azure, etc.

    # Server configuration
    port: int = 5000
    debug: bool = False
    host: str = "127.0.0.1"

    # Security configuration
    secret_key: Optional[str] = None
    api_key_required: bool = False
    allowed_origins: list = None

    # Performance configuration
    max_dialog_length: int = 1500
    max_message_length: int = 1250
    max_user_id_length: int = 256
    max_name_length: int = 50

    # Logging configuration
    log_level: str = "INFO"
    log_file: str = "logs/waifuapi.log"
    log_max_size: int = 10 * 1024 * 1024  # 10MB
    log_backup_count: int = 5

    # Pagination configuration
    default_page_size: int = 100
    max_page_size: int = 1000

    def __post_init__(self):
        if self.allowed_origins is None:
            self.allowed_origins = ["*"]


class ConfigManager:
    """Manages application configuration from various sources."""

    def __init__(self):
        self._config = None

    def load_from_env(self) -> WaifuAPIConfig:
        """
        Load configuration from environment variables.

        Returns:
            WaifuAPIConfig instance
        """
        config = WaifuAPIConfig()

        # Database configuration
        config.database_file = os.environ.get('DATABASE_FILE', config.database_file)

        # AI Model configuration
        config.model_url = os.environ.get('MODEL_URL', config.model_url)
        config.default_response = os.environ.get('DEFAULT_RESPONSE', config.default_response)
        config.default_genre = os.environ.get('DEFAULT_GENRE', config.default_genre)

        # Server configuration
        config.port = int(os.environ.get('PORT', config.port))
        config.debug = os.environ.get('DEBUG', str(config.debug)).lower() == 'true'
        config.host = os.environ.get('HOST', config.host)

        # Security configuration
        config.secret_key = os.environ.get('SECRET_KEY')
        config.api_key_required = os.environ.get('API_KEY_REQUIRED', str(config.api_key_required)).lower() == 'true'
        allowed_origins_str = os.environ.get('ALLOWED_ORIGINS')
        if allowed_origins_str:
            config.allowed_origins = [origin.strip() for origin in allowed_origins_str.split(',')]

        # Performance configuration
        config.max_dialog_length = int(os.environ.get('MAX_DIALOG_LENGTH', config.max_dialog_length))
        config.max_message_length = int(os.environ.get('MAX_MESSAGE_LENGTH', config.max_message_length))
        config.max_user_id_length = int(os.environ.get('MAX_USER_ID_LENGTH', config.max_user_id_length))
        config.max_name_length = int(os.environ.get('MAX_NAME_LENGTH', config.max_name_length))

        # Logging configuration
        config.log_level = os.environ.get('LOG_LEVEL', config.log_level)
        config.log_file = os.environ.get('LOG_FILE', config.log_file)
        config.log_max_size = int(os.environ.get('LOG_MAX_SIZE', config.log_max_size))
        config.log_backup_count = int(os.environ.get('LOG_BACKUP_COUNT', config.log_backup_count))

        # Pagination configuration
        config.default_page_size = int(os.environ.get('DEFAULT_PAGE_SIZE', config.default_page_size))
        config.max_page_size = int(os.environ.get('MAX_PAGE_SIZE', config.max_page_size))

        self._config = config
        return config

    def load_from_dict(self, config_dict: Dict[str, Any]) -> WaifuAPIConfig:
        """
        Load configuration from dictionary.

        Args:
            config_dict: Dictionary containing configuration values

        Returns:
            WaifuAPIConfig instance
        """
        # Start with default config
        config = WaifuAPIConfig()

        # Update with values from dictionary
        for key, value in config_dict.items():
            if hasattr(config, key):
                setattr(config, key, value)

        self._config = config
        return config

    def get_config(self) -> WaifuAPIConfig:
        """
        Get the current configuration.

        Returns:
            Current WaifuAPIConfig instance

        Raises:
            RuntimeError: If no configuration has been loaded
        """
        if self._config is None:
            raise RuntimeError("Configuration not loaded. Call load_from_env() or load_from_dict() first.")
        return self._config

    def validate_config(self) -> bool:
        """
        Validate the current configuration.

        Returns:
            True if configuration is valid

        Raises:
            ValueError: If configuration is invalid
        """
        if self._config is None:
            raise ValueError("No configuration loaded")

        config = self._config

        # Validate database file path
        if not config.database_file or not isinstance(config.database_file, str):
            raise ValueError("Invalid database file path")

        # Validate URLs
        if not config.model_url or not config.model_url.startswith(('http://', 'https://')):
            raise ValueError("Invalid model URL")

        # Validate lengths
        if config.max_dialog_length <= 0:
            raise ValueError("max_dialog_length must be positive")
        if config.max_message_length <= 0:
            raise ValueError("max_message_length must be positive")
        if config.max_user_id_length <= 0:
            raise ValueError("max_user_id_length must be positive")
        if config.max_name_length <= 0:
            raise ValueError("max_name_length must be positive")

        # Validate port
        if not (1 <= config.port <= 65535):
            raise ValueError("Port must be between 1 and 65535")

        # Validate pagination
        if config.default_page_size <= 0:
            raise ValueError("default_page_size must be positive")
        if config.max_page_size <= 0:
            raise ValueError("max_page_size must be positive")
        if config.default_page_size > config.max_page_size:
            raise ValueError("default_page_size cannot be greater than max_page_size")

        logger.info("Configuration validation successful")
        return True


# Global configuration manager instance
config_manager = ConfigManager()


def get_app_config() -> WaifuAPIConfig:
    """
    Get the application configuration.

    Returns:
        Current application configuration
    """
    return config_manager.get_config()


def init_app_config() -> WaifuAPIConfig:
    """
    Initialize application configuration from environment variables.

    Returns:
        Loaded configuration
    """
    config = config_manager.load_from_env()
    config_manager.validate_config()
    return config