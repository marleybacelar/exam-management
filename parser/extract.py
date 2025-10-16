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
    Extract all text and images from a PDF file with enhanced image detection.

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

        # Enhanced image extraction - try multiple methods
        # Method 1: Standard image extraction
        image_list = page.get_images(full=True)
        extracted_xrefs = set()

        for img_index, img in enumerate(image_list):
            try:
                xref = img[0]
                if xref in extracted_xrefs:
                    continue
                extracted_xrefs.add(xref)

                base_image = doc.extract_image(xref)
                image_bytes = base_image["image"]
                image_ext = base_image["ext"]

                # Save image
                image_filename = f"{pdf_name}_page{page_num + 1}_img{img_index + 1}.{image_ext}"
                image_path = os.path.join(images_dir, image_filename)

                with open(image_path, "wb") as img_file:
                    img_file.write(image_bytes)

                image_paths.append(image_filename)
                print(f"Extracted image: {image_filename}")
            except Exception as e:
                print(f"Error extracting standard image on page {page_num + 1}: {e}")

        # Method 2: Draw-based image extraction for embedded objects
        try:
            # Look for drawings that contain images (diagrams, charts, etc.)
            for drawing_index, drawing in enumerate(page.get_drawings()):
                # Check if this drawing contains raster images
                if drawing.get("items"):
                    for item in drawing["items"]:
                        if item[0] == "im":  # Image item
                            try:
                                img_xref = item[1]
                                if img_xref not in extracted_xrefs:
                                    extracted_xrefs.add(img_xref)
                                    base_image = doc.extract_image(img_xref)
                                    image_bytes = base_image["image"]
                                    image_ext = base_image["ext"]

                                    image_filename = f"{pdf_name}_page{page_num + 1}_drawing{drawing_index + 1}.{image_ext}"
                                    image_path = os.path.join(images_dir, image_filename)

                                    with open(image_path, "wb") as img_file:
                                        img_file.write(image_bytes)

                                    image_paths.append(image_filename)
                                    print(f"Extracted drawing image: {image_filename}")
                            except Exception as e:
                                print(f"Error extracting drawing image on page {page_num + 1}: {e}")
        except Exception as e:
            print(f"Error in drawing extraction on page {page_num + 1}: {e}")

        # Skip graphic extraction for now - too many errors and not adding quality images

        # Method 4: Direct bitmap extraction for pages with diagrams
        try:
            # Try to get raw pixmap and save if it contains meaningful content
            pix = page.get_pixmap()
            if pix.width > 100 and pix.height > 100:  # Skip tiny pages
                # This is a fallback - we could analyze the pixmap for diagrams
                # For now, we'll save it if it seems like it contains diagram-like content
                pix_bytes = pix.tobytes("png")
                # Heuristic: if the image is wide and tall (diagram-like), save it
                if pix.width > 400 or pix.height > 400:  # Increased threshold for better pages
                    image_filename = f"{pdf_name}_page{page_num + 1}_fullpage.png"
                    image_path = os.path.join(images_dir, image_filename)

                    with open(image_path, "wb") as img_file:
                        img_file.write(pix_bytes)

                    image_paths.append(image_filename)
                    print(f"Extracted full page diagram: {image_filename}")
        except Exception as e:
            print(f"Error extracting full page on page {page_num + 1}: {e}")

    doc.close()
    print(f"Total images extracted: {len(image_paths)}")
    return full_text, image_paths


def clean_text(text: str) -> str:
    """
    Clean and normalize extracted text.
    Remove repeated headers, footers, formatting characters, and normalize whitespace.
    """
    # Remove common ExamTopics headers/footers
    text = re.sub(r'www\.examtopics\.com', '', text, flags=re.IGNORECASE)
    text = re.sub(r'Page \d+ of \d+', '', text, flags=re.IGNORECASE)
    text = re.sub(r'Exam [A-Z]+-\d+', '', text, flags=re.IGNORECASE)

    # Remove Microsoft Certified footer text
    text = re.sub(r'Microsoft Certified.*?(?:Question Bank|Study Materials|ExamTopics).*?(?:\(|-|\d+ of \d+|$)', '', text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r'Question Bank.*?(?:\(|-|\d+ of \d+|$)', '', text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r'ExamTopics.*?(?:\(|\d+ of \d+|$)', '', text, flags=re.IGNORECASE | re.DOTALL)

    # Remove formatting characters and artifacts
    text = re.sub(r'[^\x20-\x7E\n\r\t]', '', text)  # Remove non-printable characters except basic whitespace
    text = re.sub(r'\x0c', '', text)  # Remove form feed characters
    text = re.sub(r'\x0b', '', text)  # Remove vertical tab characters

    # Remove excessive bold/formatting markers (common in PDF extraction)
    text = re.sub(r'\*\*+', '', text)  # Remove multiple asterisks
    text = re.sub(r'__+', '', text)   # Remove multiple underscores

    # Remove repeated headers and navigation text
    text = re.sub(r'(?:HOTSPOT|Case study|Overview|Existing Environment).*?(?=\n\n|\Z)', '', text, flags=re.IGNORECASE | re.DOTALL)

    # Clean up case study formatting
    text = re.sub(r'This is a case study\..*?(?=Question|\Z)', '', text, flags=re.IGNORECASE | re.DOTALL)

    # Normalize whitespace
    text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)  # Remove excessive blank lines
    text = re.sub(r' +', ' ', text)  # Remove multiple spaces
    text = re.sub(r'\n +', '\n', text)  # Remove leading spaces on lines
    text = re.sub(r' +\n', '\n', text)  # Remove trailing spaces on lines

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
