"""
Quick test script to verify PDF parsing functionality
"""

import os
from parser.extract import extract_text_and_images, clean_text
from parser.parse_questions import parse_questions_from_text, map_images_to_pages

def test_parse_pdf(pdf_path, exam_name="test_exam"):
    """Test parsing a single PDF file."""
    print(f"Testing PDF parsing for: {pdf_path}")
    print("-" * 60)
    
    # Create test exam directory
    exam_dir = f"data/{exam_name}"
    os.makedirs(exam_dir, exist_ok=True)
    
    # Extract text and images
    print("Extracting text and images...")
    pdf_name = os.path.splitext(os.path.basename(pdf_path))[0]
    full_text, image_paths = extract_text_and_images(pdf_path, exam_dir, pdf_name)
    print(f"✓ Extracted {len(image_paths)} images")
    
    # Clean text
    full_text = clean_text(full_text)
    print(f"✓ Cleaned text ({len(full_text)} characters)")
    
    # Map images to pages
    images_by_page = map_images_to_pages(full_text, image_paths)
    print(f"✓ Mapped images to {len(images_by_page)} pages")
    
    # Parse questions
    print("Parsing questions...")
    questions = parse_questions_from_text(full_text, pdf_name, images_by_page)
    print(f"✓ Parsed {len(questions)} questions")
    
    # Display sample questions
    print("\n" + "=" * 60)
    print("SAMPLE QUESTIONS:")
    print("=" * 60)
    
    for i, q in enumerate(questions[:3]):  # Show first 3 questions
        print(f"\nQuestion {i + 1}:")
        print(f"Type: {q['question_type']}")
        print(f"Text: {q['question'][:100]}...")
        print(f"Choices: {list(q['choices'].keys())}")
        print(f"PDF Answer: {q['pdf_answer']}")
        print(f"Web Answer: {q['web_recommended_answer']}")
        print(f"Images: {len(q['images'])} image(s)")
    
    # Statistics
    print("\n" + "=" * 60)
    print("STATISTICS:")
    print("=" * 60)
    
    type_counts = {}
    for q in questions:
        q_type = q.get("question_type", "unknown")
        type_counts[q_type] = type_counts.get(q_type, 0) + 1
    
    print(f"Total Questions: {len(questions)}")
    print("\nQuestion Types:")
    for q_type, count in sorted(type_counts.items()):
        print(f"  - {q_type}: {count}")
    
    print("\nTest completed successfully! ✓")
    return questions


if __name__ == "__main__":
    # Test with Part1.pdf
    pdf_path = "Part1.pdf"

    if os.path.exists(pdf_path):
        questions = test_parse_pdf(pdf_path)
    else:
        print(f"PDF file not found: {pdf_path}")
        print("Available PDF files in current directory:")
        for f in os.listdir("."):
            if f.endswith(".pdf"):
                print(f"  - {f}")
