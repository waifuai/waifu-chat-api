import requests
import re
import flask
import os
import logging

import waifuapi_db
import waifuapi_translate

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


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


def clean_paragraph(paragraph: str) -> str:
    """
    Filters a paragraph, keeping only alphanumeric characters, spaces, and certain punctuation marks.
    The function also truncates the output to the last 1250 characters.

    Args:
        paragraph: The input string (paragraph).

    Returns:
        A cleaned and truncated string.
    """
    allowed_chars = set(" '?,!")  # Use a set for faster lookup
    cleaned_paragraph = ''.join(
        char for char in paragraph if char.isalnum() or char.isspace() or char in allowed_chars
    )
    return cleaned_paragraph[-1250:]


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
    message: str = message[-1250:]
    translate_from: str = waifuapi_translate.language_defaulter(language=translate_from)
    translate_to: str = waifuapi_translate.language_defaulter(language=translate_to)

    try:
        if translate_from == 'en':
            translation_dict: dict = {}
        else:
            translation_dict: dict = waifuapi_translate.translate_text(target='en', text=message, source_language=translate_from)
            message = translation_dict.get('translatedText')
    except Exception as e:
        logging.exception("Error during translation:")
        return "Translation error. Please try again later."

    message = clean_paragraph(paragraph=message)
    situation = clean_paragraph(paragraph=situation)

    user_id: str = user_id[-256:]
    from_name: str = from_name[-20:]
    to_name: str = to_name[-20:]

    try:
        if not waifuapi_db.is_user_id_in_db(current_user=current_user, user_id=user_id):
            waifuapi_db.add_user_to_db(current_user=current_user, user_id=user_id)
    except Exception as e:
        logging.exception("Error accessing database:")
        return "Database error. Please try again later."

    dialog_old: str = waifuapi_db.get_old_dialog(current_user=current_user, user_id=user_id)

    situation = situation[-700:]
    situation = f'{situation}'
    len_dialog: int = max_len_dialog - len(situation)
    dialog_old = dialog_old[-len_dialog:]

    if from_name == '' and message == '':
        dialog_new = f'{dialog_old} {to_name} said: "'
    elif from_name == '':
        dialog_new = f'{dialog_old} You said: "{message}" {to_name} said: "'
    else:
        dialog_new = f'{dialog_old} {from_name} said: "{message}" {to_name} said: "'

    dialog_new = dialog_new[-len_dialog:]

    if from_name == '' and message == '':
        dialog_to_send = f'{dialog_old} {situation} {to_name} said: "'
    elif from_name == '':
        dialog_to_send = f'{dialog_old} {situation} You said: "{message}" {to_name} said: "'
    else:
        dialog_to_send = f'{dialog_old} {situation} {from_name} said: "{message}" {to_name} said: "'

    default_genre: str = os.environ.get("DEFAULT_GENRE", "Romance")
    dialog_to_send = f'[ Genre: {default_genre} ] {dialog_to_send}'
    dialog_to_send = dialog_to_send[-len_dialog:]

    print("sending: ", dialog_to_send)
    data: dict = {'input': dialog_to_send}
    model_url: str = os.environ.get('MODEL_URL', "http://localhost:80/path/")  # Default to localhost
    try:
        r = requests.post(model_url, data=data)
        r.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
        response: str = r.text
    except requests.exceptions.RequestException as e:
        logging.exception(f"Request to model failed: {e}")
        return "Model unavailable. Please try again later."


    if response.startswith("!DOCTYPE HTML") or response.startswith("<!DOCTYPE HTML"):
        print("error diverted")
        response = "The AI model is currently unavailable. Please try again later."

    print("response: ", response)

    dialog_to_store = dialog_new + response + '"'
    dialog_to_store = dialog_to_store[-3300:]
    try:
        waifuapi_db.update_user_dialog(current_user=current_user, user_id=user_id, dialog=dialog_to_store)
    except Exception as e:
        logging.exception("Error updating database:")
        return "Database error. Could not save conversation."

    detected_language = translation_dict.get('detectedSourceLanguage')
    print('detected source language:', detected_language)
    detected_language = waifuapi_translate.language_defaulter(detected_language)
    print('defaulted detected source language:', detected_language)
    try:
        if translate_to != 'auto':
            response = waifuapi_translate.translate_text(target=translate_to, text=response, source_language='en')
            response = response.get('translatedText')
        elif translate_from == 'auto' and detected_language == 'en':  # skip same language or will error
            pass
        elif translate_from == 'auto':
            response = waifuapi_translate.translate_text(target=detected_language, text=response, source_language='en')
            response = response.get('translatedText')
        elif translate_from == 'en':
            pass
        else:
            response = waifuapi_translate.translate_text(target=translate_from, text=response, source_language='en')
            response = response.get('translatedText')
    except Exception as e:
        logging.exception("Error during translation:")
        return "Translation error. Please try again later."

    return response


def process_form_dict(current_user: str, form_dict: dict) -> str:
    """Processes a form dictionary and returns a response."""
    if not form_dict:
        form_dict = {}

    print(form_dict)

    user_id: str = form_dict.get('user_id')
    message: str = form_dict.get('message')
    from_name: str = form_dict.get('from_name')
    to_name: str = form_dict.get('to_name')
    situation: str = form_dict.get('situation')
    translate_from: str = form_dict.get('translate_from')
    translate_to: str = form_dict.get('translate_to')

    if not user_id:
        user_id = 'default2'
    if not message:
        message = ''
    if not from_name:
        from_name = ''
    if not to_name:
        to_name = 'Waifu'
    if not situation:
        situation = ''
    if not translate_from:
        translate_from = 'auto'
    if not translate_to:
        translate_to = 'auto'

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
    return response


def print_flask_request_info(flask_request_object):
    """Prints information about a Flask request object."""
    # Add check for None before accessing attributes
    if flask_request_object:
        print('flask.request.headers:', remove_secret(flask_request_object.headers))
        print('flask.request.form:', flask_request_object.form)
        print('flask.request:', flask_request_object)
        print('flask.request.form.to_dict():', flask_request_object.form.to_dict())
        print('flask.request.args:', flask_request_object.args)
        print('flask.request.files:', flask_request_object.files)
        print('flask.request.values:', flask_request_object.values)
        print('flask.request.json:', flask_request_object.json)
        print('flask.request.data:', flask_request_object.data)
    else:
        print('flask_request_object is None')
    print('---')
