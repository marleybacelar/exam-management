"""
PDF Text and Image Extraction Module
Extracts text and images from ExamTopics-style PDFs using PyMuPDF (fitz)
"""

import fitz  # PyMuPDF
import os
import re
from typing import List, Dict, Tuple
from pathlib import Path


def extract_text_and_images(pdf_path: str, output_dir: str, pdf_name: str) -> Tuple[str, List[str]]:
    """
    Extract all text and images from a PDF file.
    
    Args:
        pdf_path: Path to the PDF file
        output_dir: Directory to save extracted images
        pdf_name: Name identifier for the PDF (for image naming)
    
    Returns:
        Tuple of (full_text, list_of_image_paths)
    """
    doc = fitz.open(pdf_path)
    full_text = ""
    image_paths = []
    
    # Create images directory if it doesn't exist
    images_dir = os.path.join(output_dir, "images")
    os.makedirs(images_dir, exist_ok=True)
    
    for page_num in range(len(doc)):
        page = doc[page_num]
        
        # Extract text
        page_text = page.get_text()
        full_text += f"\n--- PAGE {page_num + 1} ---\n"
        full_text += page_text
        
        # Extract images
        image_list = page.get_images(full=True)
        for img_index, img in enumerate(image_list):
            try:
                xref = img[0]
                base_image = doc.extract_image(xref)
                image_bytes = base_image["image"]
                image_ext = base_image["ext"]
                
                # Save image
                image_filename = f"{pdf_name}_page{page_num + 1}_img{img_index + 1}.{image_ext}"
                image_path = os.path.join(images_dir, image_filename)
                
                with open(image_path, "wb") as img_file:
                    img_file.write(image_bytes)
                
                image_paths.append(image_filename)
            except Exception as e:
                print(f"Error extracting image on page {page_num + 1}: {e}")
    
    doc.close()
    return full_text, image_paths


def clean_text(text: str) -> str:
    """
    Clean and normalize extracted text.
    Remove repeated headers, footers, and normalize whitespace.
    """
    # Remove common ExamTopics headers/footers
    text = re.sub(r'www\.examtopics\.com', '', text, flags=re.IGNORECASE)
    text = re.sub(r'Page \d+ of \d+', '', text, flags=re.IGNORECASE)
    text = re.sub(r'Exam [A-Z]+-\d+', '', text, flags=re.IGNORECASE)
    
    # Normalize whitespace
    text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)  # Remove excessive blank lines
    text = re.sub(r' +', ' ', text)  # Remove multiple spaces
    
    return text.strip()


def extract_images_for_page(doc, page_num: int, output_dir: str, pdf_name: str) -> List[str]:
    """
    Extract images from a specific page.
    
    Args:
        doc: PyMuPDF document object
        page_num: Page number (0-indexed)
        output_dir: Directory to save images
        pdf_name: PDF identifier for naming
    
    Returns:
        List of image filenames
    """
    page = doc[page_num]
    image_paths = []
    images_dir = os.path.join(output_dir, "images")
    os.makedirs(images_dir, exist_ok=True)
    
    image_list = page.get_images(full=True)
    for img_index, img in enumerate(image_list):
        try:
            xref = img[0]
            base_image = doc.extract_image(xref)
            image_bytes = base_image["image"]
            image_ext = base_image["ext"]
            
            image_filename = f"{pdf_name}_page{page_num + 1}_img{img_index + 1}.{image_ext}"
            image_path = os.path.join(images_dir, image_filename)
            
            with open(image_path, "wb") as img_file:
                img_file.write(image_bytes)
            
            image_paths.append(image_filename)
        except Exception as e:
            print(f"Error extracting image: {e}")
    
    return image_paths
