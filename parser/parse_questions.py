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
    drag_keywords = ["drag", "drop", "match", "order", "arrange", "sequence", "hotspot", "hot area"]
    if any(keyword in stem_lower for keyword in drag_keywords):
        return "input_text"  # These require text input, not selection
    
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
        
        # Remove the footer text that appears everywhere - more comprehensive pattern
        choice_text = re.sub(r'Microsoft Certified.*?(?:Question Bank|Study Materials|ExamTopics).*?(?:\(|-|\d+\s+of\s+\d+\)|$)', '', choice_text, flags=re.IGNORECASE | re.DOTALL)
        choice_text = re.sub(r'Question Bank.*?(?:\(|-|\d+\s+of\s+\d+\)|$)', '', choice_text, flags=re.IGNORECASE | re.DOTALL)
        choice_text = re.sub(r'ExamTopics.*?(?:\(|\d+\s+of\s+\d+\)|$)', '', choice_text, flags=re.IGNORECASE | re.DOTALL)
        # Remove standalone page markers like "1 of 5)" or "(1 of 5)"
        choice_text = re.sub(r'\(?\d+\s+of\s+\d+\)', '', choice_text, flags=re.IGNORECASE)
        
        # Multi-layer explanation removal - be extremely aggressive
        explanation_patterns = [
            # Layer 1: Comment phrases that start explanations
            r'^The\s+(majority|comments|community)',  # At start
            r'\s+The\s+(majority|comments|community)',   # In middle
            r'\s+the\s+(majority|comments|community)',   # Case insensitive

            # Layer 2: Common explanation starters
            r'\s+(because|since|as|therefore|however|although|while|when|where|if)\s+',  # Common explanation words
            r'\s+(agree|recommends?|suggests?|explains?|indicates?|shows?|demonstrates?)\s+',  # Action words

            # Layer 3: Colon-based explanations (ANYTHING after colon)
            r':\s*.',  # General: any colon followed by any character

            # Layer 4: Sentence-ending explanation starters
            r'\.\s+(This|It|However|Therefore|Also|While|Although|The|Since|Because|As|If|When|Where)\s+',

            # Layer 5: Direct explanation indicators
            r'\s+-\s+',  # Dash explanations
            r'\.\s+Citations',
            r'\.\s+Refer\s+to',
            r'\.\s+See\s+',
            r'\.\s+For\s+more',

            # Layer 6: Specific explanation phrases
            r'\s+AI\s+Recommended',
            r'\s+Several\s+users',
            r'\s+Many\s+comments',
            r'\s+Furthermore',
            r'\s+receives?\s+the\s+license',  # Specific to license questions
            r'\s+inherits?\s+the',  # Specific to inheritance questions

            # Layer 7: Additional explanation patterns
            r'\.\s+The\s+comments?\s+(agree|recommends?|suggests?)',  # "The comments agree..."
            r'\s+the\s+comments?\s+(agree|recommends?|suggests?)',   # Case insensitive
            r'\s+receives?\s+the\s+license\s+through',  # "receives the license through"
            r'\s+does\s+not\s+inherit',  # "does not inherit"
            r'\s+is\s+incorrect\s+because',  # "is incorrect because"
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

        # Special handling for colon patterns - remove everything after colon including the colon
        # More aggressive: if text has a colon, check if what follows is an explanation
        if ':' in choice_text:
            # Split at first colon
            parts = choice_text.split(':', 1)
            if len(parts) == 2:
                before_colon = parts[0].strip()
                after_colon = parts[1].strip()
                
                # If the text after colon is long (>30 chars) or starts with explanation words,
                # or if there's any text after colon at all (most choices shouldn't have colons),
                # it's likely an explanation, so remove it
                explanation_starters = ['this', 'while', 'although', 'however', 'because', 'since', 
                                       'the', 'it', 'management', 'creating', 'using', 'modifying',
                                       'a ', 'an ', 'is ', 'are ', 'was ', 'were ', 'will ', 'would ']
                
                # Remove explanation if:
                # 1. Text after colon is long (>30 chars)
                # 2. Starts with common explanation words
                # 3. Before colon looks like a complete answer (>10 chars)
                if (len(after_colon) > 30 or 
                    any(after_colon.lower().startswith(word) for word in explanation_starters) or
                    (len(before_colon) > 10 and len(after_colon) > 0)):
                    choice_text = before_colon
                else:
                    # Keep the full text only if it's very short (like "A: B" format)
                    choice_text = choice_text
        
        # Remove any trailing colons that might remain
        choice_text = choice_text.rstrip(':').strip()
        
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
            # Remove footer patterns
            explanation = re.sub(r'Microsoft Certified.*?(?:Question Bank|Study Materials|ExamTopics).*?(?:\(|-|\d+\s+of\s+\d+\)|$)', '', explanation, flags=re.IGNORECASE | re.DOTALL)
            explanation = re.sub(r'Question Bank.*?(?:\(|-|\d+\s+of\s+\d+\)|$)', '', explanation, flags=re.IGNORECASE | re.DOTALL)
            explanation = re.sub(r'\(?\d+\s+of\s+\d+\)', '', explanation, flags=re.IGNORECASE)
            explanation = explanation.strip()
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
    
    # Split text by question markers - capture question numbers
    # Pattern matches "Question" optionally followed by a number
    question_pattern = r'(?:^|\n)Question\s*(\d*)\s*\n'
    splits = re.split(question_pattern, text, flags=re.MULTILINE)
    
    # First element is text before first question, skip it
    if len(splits) > 1:
        splits = splits[1:]
    
    # Process each question block
    # After split, we get: [question_num, question_text, question_num, question_text, ...]
    i = 0
    question_index = 0
    while i < len(splits):
        # Get question number (might be empty string) and question block
        pdf_question_number = splits[i] if i < len(splits) else ""
        question_block = splits[i + 1] if i + 1 < len(splits) else ""
        
        # Move to next question
        i += 2
        question_index += 1
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
        
        # Remove footer patterns from question stem
        question_stem = re.sub(r'Microsoft Certified.*?(?:Question Bank|Study Materials|ExamTopics).*?(?:\(|-|\d+\s+of\s+\d+\)|$)', '', question_stem, flags=re.IGNORECASE | re.DOTALL)
        question_stem = re.sub(r'Question Bank.*?(?:\(|-|\d+\s+of\s+\d+\)|$)', '', question_stem, flags=re.IGNORECASE | re.DOTALL)
        question_stem = re.sub(r'\(?\d+\s+of\s+\d+\)', '', question_stem, flags=re.IGNORECASE)
        question_stem = question_stem.strip()
        
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
            "question_id": question_index,
            "pdf_question_number": pdf_question_number if pdf_question_number else str(question_index),
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
