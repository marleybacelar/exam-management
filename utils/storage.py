"""
Storage Utilities Module
Handles saving and loading exam data to/from disk
"""

import json
import os
from typing import List, Dict, Any, Optional
from datetime import datetime


def get_exam_dir(exam_name: str) -> str:
    """Get the directory path for a specific exam."""
    return os.path.join("data", exam_name)


def get_exam_file_path(exam_name: str) -> str:
    """Get the path to the exam JSONL file."""
    return os.path.join(get_exam_dir(exam_name), "exam.jsonl")


def get_results_dir(exam_name: str) -> str:
    """Get the results directory for a specific exam."""
    results_dir = os.path.join(get_exam_dir(exam_name), "results")
    os.makedirs(results_dir, exist_ok=True)
    return results_dir


def get_images_dir(exam_name: str) -> str:
    """Get the images directory for a specific exam."""
    images_dir = os.path.join(get_exam_dir(exam_name), "images")
    os.makedirs(images_dir, exist_ok=True)
    return images_dir


def list_exams() -> List[str]:
    """
    List all available exams.
    
    Returns:
        List of exam names
    """
    if not os.path.exists("data"):
        os.makedirs("data", exist_ok=True)
        return []
    
    exams = []
    for item in os.listdir("data"):
        exam_path = os.path.join("data", item)
        if os.path.isdir(exam_path):
            # Check if exam.jsonl exists
            if os.path.exists(os.path.join(exam_path, "exam.jsonl")):
                exams.append(item)
    
    return sorted(exams)


def exam_exists(exam_name: str) -> bool:
    """Check if an exam exists."""
    return os.path.exists(get_exam_file_path(exam_name))


def save_exam(exam_name: str, questions: List[Dict[str, Any]]) -> None:
    """
    Save exam questions to a JSONL file.
    
    Args:
        exam_name: Name of the exam
        questions: List of question dictionaries
    """
    exam_dir = get_exam_dir(exam_name)
    os.makedirs(exam_dir, exist_ok=True)
    
    exam_file = get_exam_file_path(exam_name)
    
    with open(exam_file, 'w') as f:
        for question in questions:
            f.write(json.dumps(question) + '\n')


def load_exam(exam_name: str) -> List[Dict[str, Any]]:
    """
    Load exam questions from a JSONL file.
    
    Args:
        exam_name: Name of the exam
    
    Returns:
        List of question dictionaries
    """
    exam_file = get_exam_file_path(exam_name)
    
    if not os.path.exists(exam_file):
        return []
    
    questions = []
    with open(exam_file, 'r') as f:
        for line in f:
            if line.strip():
                questions.append(json.loads(line))
    
    return questions


def append_questions_to_exam(exam_name: str, new_questions: List[Dict[str, Any]]) -> None:
    """
    Append new questions to an existing exam.
    
    Args:
        exam_name: Name of the exam
        new_questions: List of new question dictionaries to append
    """
    # Load existing questions
    existing_questions = load_exam(exam_name)
    
    # Get the max question_id
    max_id = 0
    if existing_questions:
        max_id = max(q.get("question_id", 0) for q in existing_questions)
    
    # Update question IDs for new questions
    for i, question in enumerate(new_questions):
        question["question_id"] = max_id + i + 1
    
    # Combine and save
    all_questions = existing_questions + new_questions
    save_exam(exam_name, all_questions)


def update_exam_question(exam_name: str, question_id: int, updated_question: Dict[str, Any]) -> bool:
    """
    Update a specific question in an exam.
    
    Args:
        exam_name: Name of the exam
        question_id: ID of the question to update
        updated_question: Updated question dictionary
    
    Returns:
        True if successful, False if question not found
    """
    questions = load_exam(exam_name)
    
    for i, q in enumerate(questions):
        if q.get("question_id") == question_id:
            questions[i] = updated_question
            save_exam(exam_name, questions)
            return True
    
    return False


def delete_exam(exam_name: str) -> bool:
    """
    Delete an exam and all its data.
    
    Args:
        exam_name: Name of the exam to delete
    
    Returns:
        True if successful, False otherwise
    """
    import shutil
    
    exam_dir = get_exam_dir(exam_name)
    if os.path.exists(exam_dir):
        try:
            shutil.rmtree(exam_dir)
            return True
        except Exception as e:
            print(f"Error deleting exam: {e}")
            return False
    return False


def save_exam_result(exam_name: str, score: int, total: int, answers: Dict[int, Any], 
                     details: List[Dict[str, Any]]) -> str:
    """
    Save exam attempt results.
    
    Args:
        exam_name: Name of the exam
        score: Number of correct answers
        total: Total number of questions
        answers: Dictionary mapping question_id to user answer
        details: List of detailed result for each question
    
    Returns:
        Filename of saved result
    """
    results_dir = get_results_dir(exam_name)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    result_file = os.path.join(results_dir, f"attempt_{timestamp}.json")
    
    result_data = {
        "timestamp": timestamp,
        "score": score,
        "total": total,
        "percentage": round((score / total * 100) if total > 0 else 0, 2),
        "answers": answers,
        "details": details
    }
    
    with open(result_file, 'w') as f:
        json.dump(result_data, f, indent=2)
    
    return result_file


def load_exam_results(exam_name: str) -> List[Dict[str, Any]]:
    """
    Load all exam attempt results.
    
    Args:
        exam_name: Name of the exam
    
    Returns:
        List of result dictionaries, sorted by timestamp (newest first)
    """
    results_dir = get_results_dir(exam_name)
    
    results = []
    if os.path.exists(results_dir):
        for filename in os.listdir(results_dir):
            if filename.endswith('.json'):
                filepath = os.path.join(results_dir, filename)
                try:
                    with open(filepath, 'r') as f:
                        result = json.load(f)
                        results.append(result)
                except Exception as e:
                    print(f"Error loading result {filename}: {e}")
    
    # Sort by timestamp, newest first
    results.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
    return results


def export_results_to_csv(results: List[Dict[str, Any]], output_file: str) -> None:
    """
    Export exam results to CSV format.
    
    Args:
        results: List of result dictionaries
        output_file: Path to output CSV file
    """
    import csv
    
    if not results:
        return
    
    with open(output_file, 'w', newline='') as f:
        writer = csv.writer(f)
        
        # Header
        writer.writerow(['Timestamp', 'Score', 'Total', 'Percentage'])
        
        # Data
        for result in results:
            writer.writerow([
                result.get('timestamp', ''),
                result.get('score', 0),
                result.get('total', 0),
                result.get('percentage', 0)
            ])


def get_exam_stats(exam_name: str) -> Dict[str, Any]:
    """
    Get statistics for an exam.
    
    Args:
        exam_name: Name of the exam
    
    Returns:
        Dictionary with exam statistics
    """
    questions = load_exam(exam_name)
    results = load_exam_results(exam_name)
    
    stats = {
        "total_questions": len(questions),
        "total_attempts": len(results),
        "question_types": {},
        "source_pdfs": set()
    }
    
    # Analyze questions
    for q in questions:
        q_type = q.get("question_type", "unknown")
        stats["question_types"][q_type] = stats["question_types"].get(q_type, 0) + 1
        
        source = q.get("source_pdf", "unknown")
        stats["source_pdfs"].add(source)
    
    stats["source_pdfs"] = list(stats["source_pdfs"])
    
    # Analyze attempts
    if results:
        scores = [r.get("percentage", 0) for r in results]
        stats["average_score"] = round(sum(scores) / len(scores), 2)
        stats["best_score"] = round(max(scores), 2)
        stats["worst_score"] = round(min(scores), 2)
    
    return stats
