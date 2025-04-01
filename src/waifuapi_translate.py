import google.cloud.translate_v2
import logging
from google.cloud import translate_v2 as translate # Correct import
from google.api_core import exceptions

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def translate_text(target: str, text: str, source_language: str = 'auto') -> dict:
    """Translates text into the target language.

    Args:
        target (str): The target language code (ISO 639-1).
        text (str): The text to translate.
        source_language (str, optional): The source language code (ISO 639-1). Defaults to 'auto'.

    Returns:
        dict: A dictionary containing the translated text, detected source language, and original input.
    """

    try:
        # Instantiate the client using the imported module
        translate_client = translate.Client()

        if source_language == 'en' and target == 'en':
            result: dict = {}
            print("source_language == 'en' and target == 'en'")
            result['translatedText'] = text
            result['detectedSourceLanguage'] = 'en'
            result['input'] = text
        else:
            result: dict = translate_client.translate(text, target_language=target, source_language=source_language)

        print(f"Text: {result['input']}")
        print(f"Translation: {result['translatedText']}")
        print(f"Detected source language: {result.get('detectedSourceLanguage')}")
        return result
    except exceptions.ServiceUnavailable as e:
        logging.error(f"Translation service unavailable: {e}")
        return {"translatedText": "Translation service unavailable", "detectedSourceLanguage": source_language, "input": text}
    except Exception as e:
        logging.exception(f"Error during translation:")
        return {"translatedText": "Translation error", "detectedSourceLanguage": source_language, "input": text}


def language_defaulter(language: str) -> str:
    """Returns the language code if it's supported, otherwise returns 'auto'.

    Args:
        language (str): The language code to check.

    Returns:
        str: The language code if supported, or 'auto' otherwise.
    """
    languages = {
        'af', 'sq', 'am', 'ar', 'hy', 'az', 'eu', 'be', 'bn', 'bs', 'bg', 'ca', 'ceb', 'Zh-CN', 'zh-CN', 'zh',
        'Zh-TW', 'zh-TW', 'co', 'hr', 'cs', 'da', 'nl', 'en', 'eo', 'et', 'fi', 'fr', 'fy', 'gl', 'ka', 'de',
        'el', 'gu', 'ht', 'ha', 'haw', 'he', 'iw', 'hi', 'hmn', 'hu', 'is', 'ig', 'id', 'ga', 'it', 'ja', 'jv',
        'kn', 'kk', 'km', 'rw', 'ko', 'ku', 'ky', 'lo', 'la', 'lv', 'lt', 'lb', 'mk', 'mg', 'ms', 'ml', 'mt',
        'mi', 'mr', 'mn', 'my', 'ne', 'no', 'ny', 'or', 'ps', 'fa', 'pl', 'pt', 'pa', 'ro', 'ru', 'sm', 'gd',
        'sr', 'st', 'sn', 'sd', 'si', 'sk', 'sl', 'so', 'es', 'su', 'sw', 'sv', 'tl', 'tg', 'ta', 'tt', 'te',
        'th', 'tr', 'tk', 'uk', 'ur', 'ug', 'uz', 'vi', 'cy', 'xh', 'yi', 'yo', 'zu'
    }
    return language if language in languages else 'auto'