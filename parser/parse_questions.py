"""
Question Parsing Module
Parses ExamTopics-style questions from extracted text
"""

import re
from typing import Dict, List, Optional, Any


def detect_question_type(question_stem: str, choices: Dict[str, str], has_image: bool) -> str:
    """
    Detect the type of question based on its content.
    
    Returns one of:
    - multiple_choice_single
    - multiple_choice_multiple
    - yes_no
    - image_selection
    - drag_and_drop
    - input_text
    """
    stem_lower = question_stem.lower()
    
    # Check for yes/no questions
    if len(choices) == 2:
        choice_text = " ".join(choices.values()).lower()
        if "yes" in choice_text and "no" in choice_text:
            return "yes_no"
    
    # Check for multiple answer questions
    multi_keywords = ["select two", "select three", "choose two", "choose three", 
                      "select all that apply", "choose all that apply", "select all",
                      "pick two", "pick three", "two correct", "three correct",
                      "each correct selection", "multiple answers"]
    if any(keyword in stem_lower for keyword in multi_keywords):
        return "multiple_choice_multiple"
    
    # Check for drag and drop questions
    drag_keywords = ["drag", "drop", "match", "order", "arrange", "sequence"]
    if any(keyword in stem_lower for keyword in drag_keywords):
        return "drag_and_drop"
    
    # Check for text input questions
    input_keywords = ["your answer", "_____", "fill in", "type the", "enter the"]
    if any(keyword in stem_lower for keyword in input_keywords) or len(choices) == 0:
        return "input_text"
    
    # Check for image selection questions
    if has_image and len(choices) <= 2:
        return "image_selection"
    
    # Default to single choice
    return "multiple_choice_single"


def extract_choices(text: str) -> Dict[str, str]:
    """
    Extract multiple choice options (A., B., C., D., etc.)
    Extracts only the choice text, not the explanations that follow.
    """
    choices = {}
    # Match patterns like "A. Some text" or "A) Some text"
    # Stop at next choice, or common delimiters
    pattern = r'^([A-Z])[.)]\s*(.+?)(?=^[A-Z][.)]|Microsoft Certified|Suggested Answer|Discussion|Hot Area|Note:|HOTSPOT|\Z)'
    matches = re.finditer(pattern, text, re.MULTILINE | re.DOTALL)
    
    for match in matches:
        letter = match.group(1)
        choice_text = match.group(2).strip()
        
        # Remove the footer text that appears everywhere
        choice_text = re.sub(r'Microsoft Certified: Azure Administrator Associate.*?Question Bank.*?\(.*?\)', '', choice_text, flags=re.IGNORECASE | re.DOTALL)
        
        # Look for explanation patterns - be aggressive
        # Many explanations start with common patterns or have specific indicators
        explanation_patterns = [
            # Colon-based explanations - catch ALL colons followed by explanatory text
            r':\s*[A-Z]',  # General: any colon followed by capital letter
            # Sentence endings followed by explanation starters
            r'\.\s+(This|It|However|Therefore|Also|While|Although|The|Since|Because|As|If|When|Where)\s+',
            # Direct explanation indicators
            r'\s+-\s+',  # Dash explanations like "Option A - This explains..."
            r'\.\s+Citations',
            r'\.\s+Refer\s+to',
            r'\.\s+See\s+',
            r'\.\s+For\s+more',
            # Comments that sneak in - expanded patterns
            r'^\s*The\s+(majority|comments|community)',  # Match at start of text
            r'\s+The\s+(majority|comments|community)',   # Match in middle
            r'\s+AI\s+Recommended',
            r'\s+Several\s+users',
            r'\s+Many\s+comments',
            r'\s+Furthermore',
        ]
        
        # Try to split at the first explanation pattern
        for pattern_str in explanation_patterns:
            split_match = re.search(pattern_str, choice_text, re.IGNORECASE)
            if split_match:
                choice_text = choice_text[:split_match.start()].strip()
                # Add back the period if we cut at a sentence boundary
                if not choice_text.endswith('.') and split_match.group().startswith('.'):
                    choice_text += '.'
                break
        
        # Clean up remaining whitespace
        choice_text = re.sub(r'\s+', ' ', choice_text)
        
        # Remove any trailing page markers or footers
        choice_text = re.sub(r'\s*(Microsoft Certified|Question Bank|ExamTopics).*$', '', choice_text, flags=re.IGNORECASE)
        
        # Trim trailing periods if they're artifacts
        choice_text = choice_text.rstrip('.')
        
        # Final cleanup - if the text is way too long (over 200 chars), it probably includes explanation
        # Take only up to the first period for very long options
        if len(choice_text) > 200 and '.' in choice_text:
            first_period = choice_text.find('.')
            if first_period > 20:  # Make sure we have a reasonable amount of text
                choice_text = choice_text[:first_period + 1]
        
        choices[letter] = choice_text.strip()
    
    return choices


def extract_answer(text: str, answer_type: str) -> Optional[str]:
    """
    Extract answer based on the answer type label.
    
    answer_type can be:
    - "Suggested Answer"
    - "Web Recommended Answer" or "Community Answer"
    - "AI Recommended Answer"
    """
    # Try to find the answer pattern - match only capital letters and commas, stop at first non-answer character
    patterns = [
        rf'{answer_type}:\s*([A-Z,\s]+?)(?=\n|Discussion|$)',
        rf'{answer_type}\s*:\s*([A-Z,\s]+?)(?=\n|Discussion|$)',
        rf'{answer_type}\s+([A-Z,\s]+?)(?=\n|Discussion|$)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            answer = match.group(1).strip()
            # Clean up answer - keep only A-Z letters and commas
            answer = ''.join(c for c in answer if c.isalpha() or c == ',')
            # Remove any trailing non-letter characters
            answer = re.sub(r'[^A-Z,]+$', '', answer, flags=re.IGNORECASE)
            return answer
    
    return None


def extract_explanation(text: str, explanation_type: str) -> Optional[str]:
    """
    Extract explanation text.
    
    explanation_type can be:
    - "Discussion Summary"
    - "AI Recommended Answer"
    """
    # Try to find explanation after the label
    patterns = [
        rf'{explanation_type}:\s*(.+?)(?=\n(?:Suggested Answer|Web Recommended|Community Answer|AI Recommended|Question \d+|\Z))',
        rf'{explanation_type}\s*(.+?)(?=\n(?:Suggested Answer|Web Recommended|Community Answer|AI Recommended|Question \d+|\Z))',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        if match:
            explanation = match.group(1).strip()
            # Clean up
            explanation = re.sub(r'\s+', ' ', explanation)
            return explanation
    
    return None


def parse_questions_from_text(text: str, source_pdf: str, images_by_page: Dict[int, List[str]]) -> List[Dict[str, Any]]:
    """
    Parse questions from extracted PDF text.
    
    Args:
        text: Full extracted text
        source_pdf: Name of source PDF file
        images_by_page: Dictionary mapping page numbers to list of image filenames
    
    Returns:
        List of question dictionaries
    """
    questions = []
    
    # Split text by question markers - updated to handle "Question" without numbers
    question_pattern = r'(?:^|\n)Question\s*\n'
    splits = re.split(question_pattern, text, flags=re.MULTILINE)
    
    # First element is text before first question, skip it
    if len(splits) > 1:
        splits = splits[1:]
    
    # Process each question block
    for i, question_block in enumerate(splits):
        if not question_block.strip():
            continue
        
        # Extract page number if present
        page_match = re.search(r'--- PAGE (\d+) ---', question_block)
        page_number = int(page_match.group(1)) if page_match else 1
        
        # Remove page markers
        question_block = re.sub(r'--- PAGE \d+ ---', '', question_block)
        
        # Split into main question and metadata
        # Look for the first choice (A.) to separate question stem from choices
        choice_start = re.search(r'\n([A-Z])[.)]\s+', question_block)
        
        if choice_start:
            question_stem = question_block[:choice_start.start()].strip()
            rest_of_block = question_block[choice_start.start():].strip()
        else:
            # No choices found, might be a text input question
            question_stem = question_block.strip()
            rest_of_block = ""
        
        # Clean question stem by removing answer sections
        # Remove everything after "Suggested Answer", "Discussion Summary", or "AI Recommended Answer"
        answer_markers = [
            "Suggested Answer:",
            "Discussion Summary",
            "AI Recommended Answer",
            "Web Recommended Answer",
            "Community Answer"
        ]
        for marker in answer_markers:
            marker_pos = question_stem.find(marker)
            if marker_pos != -1:
                question_stem = question_stem[:marker_pos].strip()
                break
        
        # Extract choices
        choices = extract_choices(rest_of_block)
        
        # Get images for this question's page
        question_images = images_by_page.get(page_number, [])
        
        # Extract answers
        pdf_answer = extract_answer(question_block, "Suggested Answer")
        web_answer = extract_answer(question_block, "Web Recommended Answer") or \
                     extract_answer(question_block, "Community Answer")
        ai_answer = extract_answer(question_block, "AI Recommended Answer")
        
        # Extract explanations
        web_explanation = extract_explanation(question_block, "Discussion Summary")
        ai_explanation = extract_explanation(question_block, "AI Recommended Answer")
        
        # Detect question type
        has_image = len(question_images) > 0
        question_type = detect_question_type(question_stem, choices, has_image)
        
        # Build question object
        question_obj = {
            "question_id": len(questions) + 1,
            "source_pdf": source_pdf,
            "page_number": page_number,
            "question_type": question_type,
            "question": question_stem,
            "choices": choices,
            "pdf_answer": pdf_answer or "",
            "web_recommended_answer": web_answer or "",
            "ai_recommended_answer": ai_answer or "",
            "web_explanation": web_explanation or "",
            "ai_explanation": ai_explanation or "",
            "images": question_images,
            "user_answer": None
        }
        
        questions.append(question_obj)
    
    return questions


def map_images_to_pages(text: str, all_images: List[str]) -> Dict[int, List[str]]:
    """
    Map images to their page numbers based on page markers in text.
    
    Args:
        text: Full extracted text with page markers
        all_images: List of all image filenames
    
    Returns:
        Dictionary mapping page numbers to list of images
    """
    images_by_page = {}
    
    # Extract page numbers from image filenames
    for image_name in all_images:
        # Pattern: {pdf_name}_page{num}_img{num}.{ext}
        match = re.search(r'_page(\d+)_img\d+', image_name)
        if match:
            page_num = int(match.group(1))
            if page_num not in images_by_page:
                images_by_page[page_num] = []
            images_by_page[page_num].append(image_name)
    
    return images_by_page
