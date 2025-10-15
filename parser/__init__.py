"""
Parser package for extracting and parsing exam questions from PDFs
"""

from .extract import extract_text_and_images, clean_text
from .parse_questions import (
    parse_questions_from_text,
    map_images_to_pages,
    detect_question_type,
    extract_choices,
    extract_answer,
    extract_explanation
)

__all__ = [
    'extract_text_and_images',
    'clean_text',
    'parse_questions_from_text',
    'map_images_to_pages',
    'detect_question_type',
    'extract_choices',
    'extract_answer',
    'extract_explanation'
]
