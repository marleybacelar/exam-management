"""
Diagnostic script to examine PDF text format
"""

import os
from parser.extract import extract_text_and_images, clean_text

def diagnose_pdf_format(pdf_path):
    """Examine the actual format of the PDF text."""
    print(f"Diagnosing PDF format: {pdf_path}")
    print("=" * 60)
    
    # Extract text
    exam_dir = "data/diagnostic"
    os.makedirs(exam_dir, exist_ok=True)
    
    pdf_name = os.path.splitext(os.path.basename(pdf_path))[0]
    full_text, _ = extract_text_and_images(pdf_path, exam_dir, pdf_name)
    full_text = clean_text(full_text)
    
    # Show first 5000 characters
    print("\nFirst 5000 characters of cleaned text:")
    print("-" * 60)
    print(full_text[:5000])
    print("-" * 60)
    
    # Look for question patterns
    print("\nSearching for common patterns...")
    print("-" * 60)
    
    import re
    
    # Various question patterns to try
    patterns = [
        (r'Question\s+#?(\d+)', "Question #N or Question N"),
        (r'Q\s*(\d+)', "Q N"),
        (r'^\d+\.\s+', "N. (at line start)"),
        (r'QUESTION\s+(\d+)', "QUESTION N (uppercase)"),
    ]
    
    for pattern, description in patterns:
        matches = re.findall(pattern, full_text, re.MULTILINE | re.IGNORECASE)
        print(f"{description}: Found {len(matches)} matches")
        if matches:
            print(f"  First few: {matches[:5]}")
    
    # Look for answer patterns
    print("\nSearching for answer patterns...")
    print("-" * 60)
    
    answer_patterns = [
        (r'Suggested Answer:\s*([A-Z])', "Suggested Answer: X"),
        (r'Correct Answer:\s*([A-Z])', "Correct Answer: X"),
        (r'Answer:\s*([A-Z])', "Answer: X"),
        (r'Community vote distribution', "Community vote"),
    ]
    
    for pattern, description in patterns:
        matches = re.findall(pattern, full_text, re.MULTILINE | re.IGNORECASE)
        if matches:
            print(f"{description}: Found {len(matches)} matches")


if __name__ == "__main__":
    pdf_path = "pdfs/az-104/Part1.pdf"
    if os.path.exists(pdf_path):
        diagnose_pdf_format(pdf_path)
    else:
        print(f"PDF not found: {pdf_path}")
