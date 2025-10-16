"""Quick test for parser improvements"""
import json
import os
import sys
from io import StringIO
from parser.extract import extract_text_and_images, clean_text
from parser.parse_questions import parse_questions_from_text, map_images_to_pages

# Parse the PDF (suppress image extraction output)
exam_dir = 'data/test_exam'
pdf_name = 'Part1'

old_stdout = sys.stdout
sys.stdout = StringIO()

full_text, image_paths = extract_text_and_images('Part1.pdf', exam_dir, pdf_name)
full_text = clean_text(full_text)
images_by_page = map_images_to_pages(full_text, image_paths)
questions = parse_questions_from_text(full_text, pdf_name, images_by_page)

sys.stdout = old_stdout

print('=' * 80)
print('PDF QUESTION NUMBER EXTRACTION TEST')
print('=' * 80)
for q in questions[:10]:
    print(f"ID: {q['question_id']:3d} | PDF #: {q.get('pdf_question_number', 'N/A'):>3s} | Source: {q['source_pdf']}")

print()
print('=' * 80)
print('CHOICE CLEANING TEST - Question 1')
print('=' * 80)
q1 = questions[0]
print('Question:', q1['question'][:100] + '...')
print()
print('Choices:')
for key, val in q1['choices'].items():
    print(f'{key}. {val}')

print()
print('=' * 80)
print('CHOICE CLEANING TEST - Question 5')
print('=' * 80)
q5 = questions[4]
print('Question:', q5['question'][:100] + '...')
print()
print('Choices:')
for key, val in q5['choices'].items():
    print(f'{key}. {val}')

print()
print('=' * 80)
print('QUESTION 24 - Footer Test')
print('=' * 80)
q24 = [q for q in questions if q['question_id'] == 24][0]
print('Question ends with:', q24['question'][-80:])
print()
print('Choice A:', q24['choices']['A'])
print('Choice B:', q24['choices']['B'])

print()
print('=' * 80)
print('SUMMARY')
print('=' * 80)
print(f"✓ Total questions parsed: {len(questions)}")
print(f"✓ PDF question numbers extracted: {questions[0].get('pdf_question_number', 'N/A')}, {questions[1].get('pdf_question_number', 'N/A')}, {questions[2].get('pdf_question_number', 'N/A')}")
print(f"✓ Footer '5)' removed: {'5)' not in q24['question']}")

# Check if colons are removed from choices
colons_in_choices = sum(1 for q in questions for c in q['choices'].values() if ':' in c)
print(f"⚠ Choices with colons remaining: {colons_in_choices}")
