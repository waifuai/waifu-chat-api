"""
Input validation and sanitization utilities for WaifuAPI.
"""
import re
import string
from typing import Dict, Any, List, Optional, Union
from .waifuapi_logging import get_logger, WaifuAPIError

logger = get_logger("validation")


class ValidationError(WaifuAPIError):
    """Raised when input validation fails."""
    pass


def sanitize_text(text: str, max_length: int = 1000, allow_newlines: bool = True) -> str:
    """
    Sanitize text input by removing potentially harmful characters.

    Args:
        text: Input text to sanitize
        max_length: Maximum allowed length
        allow_newlines: Whether to allow newline characters

    Returns:
        Sanitized text

    Raises:
        ValidationError: If text is invalid
    """
    if not isinstance(text, str):
        raise ValidationError("Input must be a string", 400, "INVALID_TYPE")

    # Remove null bytes and other control characters (except newlines if allowed)
    if allow_newlines:
        allowed_chars = string.printable + '\n\r\t'
    else:
        allowed_chars = string.printable

    # Remove null bytes and other dangerous characters
    sanitized = ''.join(char for char in text if char in allowed_chars and ord(char) >= 32)

    # Trim whitespace
    sanitized = sanitized.strip()

    # Check length
    if len(sanitized) > max_length:
        raise ValidationError(f"Text exceeds maximum length of {max_length}", 400, "TEXT_TOO_LONG")

    return sanitized


def validate_user_id(user_id: str) -> str:
    """
    Validate and sanitize user ID.

    Args:
        user_id: User ID to validate

    Returns:
        Validated user ID

    Raises:
        ValidationError: If user ID is invalid
    """
    if not user_id:
        raise ValidationError("User ID is required", 400, "MISSING_USER_ID")

    if not isinstance(user_id, str):
        raise ValidationError("User ID must be a string", 400, "INVALID_USER_ID_TYPE")

    # Sanitize and validate length
    sanitized = sanitize_text(user_id, max_length=256, allow_newlines=False)

    # Check for valid characters (alphanumeric, underscore, dash)
    if not re.match(r'^[a-zA-Z0-9_-]+$', sanitized):
        raise ValidationError("User ID contains invalid characters", 400, "INVALID_USER_ID_FORMAT")

    return sanitized


def validate_message(message: str) -> str:
    """
    Validate and sanitize chat message.

    Args:
        message: Message to validate

    Returns:
        Validated message

    Raises:
        ValidationError: If message is invalid
    """
    if not isinstance(message, str):
        raise ValidationError("Message must be a string", 400, "INVALID_MESSAGE_TYPE")

    # Sanitize message
    sanitized = sanitize_text(message, max_length=1250, allow_newlines=True)

    if not sanitized:
        raise ValidationError("Message cannot be empty", 400, "EMPTY_MESSAGE")

    return sanitized


def validate_dialog_json(dialog_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Validate dialog JSON structure.

    Args:
        dialog_data: Dialog data to validate

    Returns:
        Validated dialog data

    Raises:
        ValidationError: If dialog data is invalid
    """
    if not isinstance(dialog_data, dict):
        raise ValidationError("Dialog data must be a dictionary", 400, "INVALID_DIALOG_TYPE")

    if "dialog" not in dialog_data:
        raise ValidationError("Dialog data must contain 'dialog' key", 400, "MISSING_DIALOG_KEY")

    dialog_list = dialog_data["dialog"]
    if not isinstance(dialog_list, list):
        raise ValidationError("Dialog must be a list", 400, "INVALID_DIALOG_LIST")

    if len(dialog_list) > 1000:
        raise ValidationError("Dialog list too long", 400, "DIALOG_TOO_LONG")

    validated_dialog = []
    for i, entry in enumerate(dialog_list):
        if not isinstance(entry, dict):
            raise ValidationError(f"Dialog entry {i} must be a dictionary", 400, "INVALID_DIALOG_ENTRY")

        required_keys = {"index", "name", "message"}
        if not all(key in entry for key in required_keys):
            raise ValidationError(f"Dialog entry {i} missing required keys", 400, "MISSING_DIALOG_KEYS")

        # Validate each field
        name = sanitize_text(str(entry["name"]), max_length=50, allow_newlines=False)
        message = validate_message(str(entry["message"]))

        validated_entry = {
            "index": int(entry["index"]),
            "name": name,
            "message": message
        }
        validated_dialog.append(validated_entry)

    return validated_dialog


def validate_pagination_params(page: int, page_size: int = 100) -> tuple[int, int]:
    """
    Validate pagination parameters.

    Args:
        page: Page number (0-indexed)
        page_size: Number of items per page

    Returns:
        Tuple of (page, page_size)

    Raises:
        ValidationError: If parameters are invalid
    """
    if not isinstance(page, int) or page < 0:
        raise ValidationError("Page must be a non-negative integer", 400, "INVALID_PAGE")

    if not isinstance(page_size, int) or page_size < 1 or page_size > 1000:
        raise ValidationError("Page size must be between 1 and 1000", 400, "INVALID_PAGE_SIZE")

    return page, page_size


def validate_language_code(language: str) -> str:
    """
    Validate language code.

    Args:
        language: Language code to validate

    Returns:
        Validated language code

    Raises:
        ValidationError: If language code is invalid
    """
    if not isinstance(language, str):
        raise ValidationError("Language code must be a string", 400, "INVALID_LANGUAGE_TYPE")

    # Common language codes (subset of ISO 639-1)
    valid_languages = {
        'en', 'es', 'fr', 'de', 'it', 'pt', 'ru', 'ja', 'ko', 'zh', 'ar', 'hi',
        'auto', 'zh-CN', 'zh-TW', 'pt-BR', 'pt-PT'
    }

    language_lower = language.lower()
    if language_lower not in valid_languages:
        raise ValidationError(f"Unsupported language code: {language}", 400, "UNSUPPORTED_LANGUAGE")

    return language_lower


def validate_form_dict(form_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate and sanitize form dictionary.

    Args:
        form_dict: Form data to validate

    Returns:
        Validated and sanitized form data

    Raises:
        ValidationError: If form data is invalid
    """
    if not isinstance(form_dict, dict):
        raise ValidationError("Form data must be a dictionary", 400, "INVALID_FORM_TYPE")

    validated = {}

    # Validate user_id if present
    if "user_id" in form_dict:
        validated["user_id"] = validate_user_id(form_dict["user_id"])

    # Validate message if present
    if "message" in form_dict:
        validated["message"] = validate_message(form_dict["message"])

    # Validate optional fields
    optional_fields = ["from_name", "to_name", "situation", "translate_from", "translate_to"]
    for field in optional_fields:
        if field in form_dict and form_dict[field]:
            if field.startswith("translate"):
                validated[field] = validate_language_code(form_dict[field])
            else:
                validated[field] = sanitize_text(str(form_dict[field]), max_length=256, allow_newlines=False)

    return validated


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename to prevent path traversal attacks.

    Args:
        filename: Filename to sanitize

    Returns:
        Sanitized filename

    Raises:
        ValidationError: If filename is invalid
    """
    if not isinstance(filename, str):
        raise ValidationError("Filename must be a string", 400, "INVALID_FILENAME_TYPE")

    # Remove path separators and dangerous characters
    sanitized = re.sub(r'[<>:"/\\|?*]', '', filename)

    # Remove control characters
    sanitized = ''.join(char for char in sanitized if ord(char) >= 32)

    # Trim whitespace
    sanitized = sanitized.strip()

    if not sanitized:
        raise ValidationError("Filename cannot be empty", 400, "EMPTY_FILENAME")

    if len(sanitized) > 255:
        raise ValidationError("Filename too long", 400, "FILENAME_TOO_LONG")

    return sanitized