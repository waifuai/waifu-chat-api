import requests
import re
import flask
import os
import logging

import waifuapi_translate

from .waifuapi_logging import get_logger, handle_exception
from .waifuapi_config import get_app_config
from .waifuapi_validation import sanitize_text, alnum_crop
from .waifuapi_db_pool import (
    get_old_dialog, update_user_dialog, is_user_id_in_db, add_user_to_db
)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = get_logger("process")


def remove_secret(header: str) -> str:
    """Removes lines containing '-Secret:' from a header string."""
    if not header or not isinstance(header, str):
        logging.exception("Error in remove_secret: Input is not a string.")
        return header

    lines = header.splitlines()
    filtered_lines = [line for line in lines if "-Secret:" not in line
]
    return "\n".join(filtered_lines)


def case_sensitive_replace(s: str, before: str, after: str) -> str:
    """Replaces 'before' with 'after' in 's', preserving case."""

    def replace_case(match):
        matched_text = match.group(0)
        result = ""
        for i in range(len(matched_text)):
            if i < len(after):
                if matched_text[i].isupper():
                    result += after[i].upper()
                elif matched_text[i].islower():
                    result += after[i].lower()
                else:
                    result += after[i]
            else:
                #If before is longer than after, keep original chars
                break
        
        # Pad with remaining 'after' chars if 'after' string is longer
        if len(after) > len(matched_text):
            result += after[len(matched_text):]

        return result

    return re.sub(re.escape(before), replace_case, s, flags=re.I)


# These functions are now moved to waifuapi_validation.py
# Keeping backward compatibility imports
def clean_paragraph(paragraph: str) -> str:
    """
    Filters a paragraph, keeping only alphanumeric characters, spaces, and certain punctuation marks.
    The function also truncates the output to the last 1250 characters.

    Args:
        paragraph: The input string (paragraph).

    Returns:
        A cleaned and truncated string.
    """
    return sanitize_text(paragraph, max_length=1250, allow_newlines=True)


def alnum_crop(input_str: str, max_len: int) -> str:
    """Crops the input string to max_len, keeping only alphanumeric characters.

    The function iterates through the input string, filters out non-alphanumeric
    characters, and returns the last `max_len` characters of the filtered string.
    """
    filtered_str = "".join(char for char in input_str if char.isalnum())
    return filtered_str[-max_len:]

def process_message(
        current_user: str,
        user_id: str,
        message: str,
        from_name: str,
        to_name: str,
        situation: str,
        translate_from: str,
        translate_to: str,
        max_len_dialog: int = 1500,
) -> str:
    """Processes a message and returns a response."""
    try:
        config = get_app_config()
        max_message_length = config.max_message_length
        max_user_id_length = config.max_user_id_length
        max_name_length = config.max_name_length
    except Exception:
        # Fallback to defaults if config not available
        max_message_length = 1250
        max_user_id_length = 256
        max_name_length = 50

    # Sanitize inputs
    message = message[-max_message_length:]
    user_id = user_id[-max_user_id_length:]
    from_name = from_name[-max_name_length:]
    to_name = to_name[-max_name_length:]

    # Validate and default language codes
    translate_from = waifuapi_translate.language_defaulter(language=translate_from)
    translate_to = waifuapi_translate.language_defaulter(language=translate_to)

    try:
        if translate_from == 'en':
            translation_dict: dict = {}
        else:
            logger.debug(f"Translating message from {translate_from} to en")
            translation_dict = waifuapi_translate.translate_text(
                target='en',
                text=message,
                source_language=translate_from
            )
            message = translation_dict.get('translatedText', message)
    except Exception as e:
        logger.error(f"Error during translation: {e}")
        return "Translation error. Please try again later."

    # Clean and validate inputs
    message = clean_paragraph(paragraph=message)
    situation = clean_paragraph(paragraph=situation)

    try:
        if not waifuapi_db.is_user_id_in_db(current_user=current_user, user_id=user_id):
            logger.info(f"Creating new user: {user_id} for current_user: {current_user}")
            waifuapi_db.add_user_to_db(current_user=current_user, user_id=user_id)
    except Exception as e:
        logger.error(f"Error accessing database for user {user_id}: {e}")
        return "Database error. Please try again later."

    dialog_old: str = waifuapi_db.get_old_dialog(current_user=current_user, user_id=user_id)

    # Prepare dialog context
    situation = situation[-700:]
    situation = f'{situation}'
    len_dialog: int = max_len_dialog - len(situation)
    dialog_old = dialog_old[-len_dialog:]

    # Build new dialog entry
    if from_name == '' and message == '':
        dialog_new = f'{dialog_old} {to_name} said: "'
    elif from_name == '':
        dialog_new = f'{dialog_old} You said: "{message}" {to_name} said: "'
    else:
        dialog_new = f'{dialog_old} {from_name} said: "{message}" {to_name} said: "'

    dialog_new = dialog_new[-len_dialog:]

    # Build dialog to send to model
    if from_name == '' and message == '':
        dialog_to_send = f'{dialog_old} {situation} {to_name} said: "'
    elif from_name == '':
        dialog_to_send = f'{dialog_old} {situation} You said: "{message}" {to_name} said: "'
    else:
        dialog_to_send = f'{dialog_old} {situation} {from_name} said: "{message}" {to_name} said: "'

    # Add genre from configuration
    try:
        config = get_app_config()
        default_genre = config.default_genre
        model_url = config.model_url
    except Exception:
        default_genre = "Romance"
        model_url = "http://localhost:80/path/"

    dialog_to_send = f'[ Genre: {default_genre} ] {dialog_to_send}'
    dialog_to_send = dialog_to_send[-len_dialog:]

    logger.debug(f"Sending dialog to model: {dialog_to_send[:100]}...")
    data: dict = {'input': dialog_to_send}

    try:
        r = requests.post(model_url, data=data, timeout=30)
        r.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
        response: str = r.text
    except requests.exceptions.Timeout:
        logger.error("Request to model timed out")
        return "Model is taking too long to respond. Please try again later."
    except requests.exceptions.ConnectionError:
        logger.error("Connection error to model")
        return "Cannot connect to AI model. Please try again later."
    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTP error from model: {e}")
        return "AI model returned an error. Please try again later."
    except requests.exceptions.RequestException as e:
        logger.error(f"Request to model failed: {e}")
        return "Model unavailable. Please try again later."


    # Check for HTML error responses
    if response.startswith("!DOCTYPE HTML") or response.startswith("<!DOCTYPE HTML"):
        logger.warning("Received HTML error response from model")
        response = "The AI model is currently unavailable. Please try again later."

    logger.debug(f"Model response: {response[:100]}...")

    # Store conversation in database
    dialog_to_store = dialog_new + response + '"'
    dialog_to_store = dialog_to_store[-3300:]
    try:
        waifuapi_db.update_user_dialog(current_user=current_user, user_id=user_id, dialog=dialog_to_store)
        logger.info(f"Conversation updated for user: {user_id}")
    except Exception as e:
        logger.error(f"Error updating database for user {user_id}: {e}")
        return "Database error. Could not save conversation."

    # Handle translation back to original language
    detected_language = translation_dict.get('detectedSourceLanguage')
    logger.debug(f'Detected source language: {detected_language}')
    detected_language = waifuapi_translate.language_defaulter(detected_language)
    logger.debug(f'Defaulted detected source language: {detected_language}')

    try:
        if translate_to != 'auto':
            logger.debug(f"Translating response to {translate_to}")
            translation_result = waifuapi_translate.translate_text(
                target=translate_to, text=response, source_language='en'
            )
            response = translation_result.get('translatedText', response)
        elif translate_from == 'auto' and detected_language == 'en':
            # Skip same language translation
            logger.debug("Skipping translation - same language")
            pass
        elif translate_from == 'auto':
            logger.debug(f"Translating response to detected language: {detected_language}")
            translation_result = waifuapi_translate.translate_text(
                target=detected_language, text=response, source_language='en'
            )
            response = translation_result.get('translatedText', response)
        elif translate_from == 'en':
            # No translation needed
            logger.debug("No translation needed - English to English")
            pass
        else:
            logger.debug(f"Translating response to original language: {translate_from}")
            translation_result = waifuapi_translate.translate_text(
                target=translate_from, text=response, source_language='en'
            )
            response = translation_result.get('translatedText', response)
    except Exception as e:
        logger.error(f"Error during response translation: {e}")
        return "Translation error. Please try again later."

    return response


def process_form_dict(current_user: str, form_dict: dict) -> str:
    """Processes a form dictionary and returns a response."""
    if not form_dict:
        form_dict = {}

    logger.debug(f"Processing form data: {list(form_dict.keys())}")

    # Extract form data with defaults
    user_id: str = form_dict.get('user_id', 'default2')
    message: str = form_dict.get('message', '')
    from_name: str = form_dict.get('from_name', '')
    to_name: str = form_dict.get('to_name', 'Waifu')
    situation: str = form_dict.get('situation', '')
    translate_from: str = form_dict.get('translate_from', 'auto')
    translate_to: str = form_dict.get('translate_to', 'auto')

    # Validate required fields
    if not user_id:
        logger.warning("Empty user_id provided, using default")
        user_id = 'default2'

    logger.info(f"Processing chat request for user: {user_id}")

    response: str = process_message(
        current_user=current_user,
        user_id=user_id,
        message=message,
        from_name=from_name,
        to_name=to_name,
        situation=situation,
        translate_from=translate_from,
        translate_to=translate_to,
    )

    logger.info(f"Chat response generated for user: {user_id}")
    return response


def log_request_info(flask_request_object, logger=None):
    """Logs information about a Flask request object."""
    if logger is None:
        logger = get_logger("request")

    # Add check for None before accessing attributes
    if flask_request_object:
        logger.debug('Request headers: %s', remove_secret(flask_request_object.headers))
        logger.debug('Request form: %s', flask_request_object.form)
        logger.debug('Request method: %s', flask_request_object.method)
        logger.debug('Request URL: %s', flask_request_object.url)
        logger.debug('Request form dict: %s', flask_request_object.form.to_dict())
        logger.debug('Request args: %s', flask_request_object.args)
        logger.debug('Request files: %s', flask_request_object.files)
        logger.debug('Request values: %s', flask_request_object.values)
        logger.debug('Request JSON: %s', flask_request_object.json)
        logger.debug('Request data: %s', flask_request_object.data)
    else:
        logger.debug('flask_request_object is None')
