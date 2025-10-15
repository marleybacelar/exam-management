"""
Multi-Exam Streamlit Application
Main application file for managing and taking ExamTopics-style exams
"""

import streamlit as st
import os
import re
from typing import Dict, Any, List
import pandas as pd
from datetime import datetime

# Import custom modules
from parser.extract import extract_text_and_images, clean_text
from parser.parse_questions import parse_questions_from_text, map_images_to_pages
from utils.storage import (
    list_exams, load_exam, save_exam, delete_exam, exam_exists,
    append_questions_to_exam, update_exam_question, save_exam_result,
    load_exam_results, get_exam_stats, get_exam_dir, get_images_dir
)


# Page configuration
st.set_page_config(
    page_title="Exam Management System",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)


def check_password():
    """
    Check if user is authenticated.
    Returns True if password is correct or not set.
    """
    # Get password from environment variable
    correct_password = os.environ.get("APP_PASSWORD", None)
    
    # If no password is set, allow access
    if not correct_password:
        return True
    
    # Initialize session state for authentication
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    
    # If already authenticated, return True
    if st.session_state.authenticated:
        return True
    
    # Show password input
    st.title("🔒 Authentication Required")
    st.markdown("Please enter the password to access the Exam Management System.")
    
    password = st.text_input("Password", type="password", key="password_input")
    
    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        if st.button("Login", type="primary"):
            if password == correct_password:
                st.session_state.authenticated = True
                st.success("✅ Access granted!")
                st.rerun()
            else:
                st.error("❌ Incorrect password. Please try again.")
    
    return False


def initialize_session_state():
    """Initialize session state variables."""
    if "current_page" not in st.session_state:
        st.session_state.current_page = "home"
    if "selected_exam" not in st.session_state:
        st.session_state.selected_exam = None
    if "current_question_index" not in st.session_state:
        st.session_state.current_question_index = 0
    if "current_page_num" not in st.session_state:
        st.session_state.current_page_num = 0
    if "questions_per_page" not in st.session_state:
        st.session_state.questions_per_page = 100
    if "user_answers" not in st.session_state:
        st.session_state.user_answers = {}
    if "exam_submitted" not in st.session_state:
        st.session_state.exam_submitted = False
    if "exam_questions" not in st.session_state:
        st.session_state.exam_questions = []


def home_page():
    """Display the home page with exam list."""
    st.title("📚 Exam Management System")
    st.markdown("### Manage and take ExamTopics-style certification exams")
    
    # Create new exam button
    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        if st.button("➕ Create New Exam", use_container_width=True):
            st.session_state.current_page = "create_exam"
            st.rerun()
    
    st.markdown("---")
    
    # List existing exams
    exams = list_exams()
    
    if not exams:
        st.info("No exams found. Create your first exam to get started!")
    else:
        st.subheader(f"Your Exams ({len(exams)})")
        
        for exam_name in exams:
            with st.container():
                col1, col2, col3, col4, col5 = st.columns([3, 1, 1, 1, 1])
                
                with col1:
                    # Get exam stats
                    stats = get_exam_stats(exam_name)
                    st.markdown(f"### 📖 {exam_name}")
                    st.caption(f"{stats['total_questions']} questions | {stats['total_attempts']} attempts")
                
                with col2:
                    if st.button("📝 Take Exam", key=f"take_{exam_name}"):
                        st.session_state.selected_exam = exam_name
                        st.session_state.current_page = "take_exam"
                        st.session_state.current_question_index = 0
                        st.session_state.user_answers = {}
                        st.session_state.exam_submitted = False
                        st.session_state.exam_questions = load_exam(exam_name)
                        st.rerun()
                
                with col3:
                    if st.button("✏️ Edit", key=f"edit_{exam_name}"):
                        st.session_state.selected_exam = exam_name
                        st.session_state.current_page = "edit_exam"
                        st.rerun()
                
                with col4:
                    if st.button("📊 Results", key=f"results_{exam_name}"):
                        st.session_state.selected_exam = exam_name
                        st.session_state.current_page = "view_results"
                        st.rerun()
                
                with col5:
                    if st.button("🗑️ Delete", key=f"delete_{exam_name}"):
                        if delete_exam(exam_name):
                            st.success(f"Deleted exam: {exam_name}")
                            st.rerun()
                        else:
                            st.error("Failed to delete exam")
                
                st.markdown("---")


def create_exam_page():
    """Page for creating a new exam."""
    st.title("➕ Create New Exam")
    
    if st.button("⬅️ Back to Home"):
        st.session_state.current_page = "home"
        st.rerun()
    
    st.markdown("---")
    
    # Exam name input
    exam_name = st.text_input(
        "Exam Name",
        placeholder="e.g., Azure Administrator AZ-104",
        help="Enter a unique name for this exam"
    )
    
    # PDF upload
    uploaded_files = st.file_uploader(
        "Upload PDF Files",
        type=["pdf"],
        accept_multiple_files=True,
        help="Upload one or more ExamTopics-style PDF files"
    )
    
    # Options
    col1, col2 = st.columns(2)
    with col1:
        append_to_existing = st.checkbox(
            "Append to existing exam",
            help="Add questions to an existing exam instead of creating new"
        )
    
    if append_to_existing:
        existing_exams = list_exams()
        if existing_exams:
            exam_name = st.selectbox("Select Exam", existing_exams)
        else:
            st.warning("No existing exams found")
            append_to_existing = False
    
    # Parse button
    if st.button("🔄 Parse and Save Exam", type="primary", disabled=not uploaded_files or not exam_name):
        if uploaded_files and exam_name:
            with st.spinner("Parsing PDFs... This may take a few minutes."):
                try:
                    all_questions = []
                    progress_bar = st.progress(0)
                    
                    for idx, uploaded_file in enumerate(uploaded_files):
                        st.info(f"Processing: {uploaded_file.name}")
                        
                        # Save uploaded file temporarily
                        temp_pdf_path = f"temp_{uploaded_file.name}"
                        with open(temp_pdf_path, "wb") as f:
                            f.write(uploaded_file.read())
                        
                        # Extract text and images
                        exam_dir = get_exam_dir(exam_name)
                        pdf_name = os.path.splitext(uploaded_file.name)[0]
                        
                        full_text, image_paths = extract_text_and_images(
                            temp_pdf_path,
                            exam_dir,
                            pdf_name
                        )
                        
                        # Clean text
                        full_text = clean_text(full_text)
                        
                        # Map images to pages
                        images_by_page = map_images_to_pages(full_text, image_paths)
                        
                        # Parse questions
                        questions = parse_questions_from_text(
                            full_text,
                            uploaded_file.name,
                            images_by_page
                        )
                        
                        all_questions.extend(questions)
                        
                        # Clean up temp file
                        os.remove(temp_pdf_path)
                        
                        # Update progress
                        progress_bar.progress((idx + 1) / len(uploaded_files))
                    
                    # Save or append questions
                    if append_to_existing and exam_exists(exam_name):
                        append_questions_to_exam(exam_name, all_questions)
                        st.success(f"✅ Added {len(all_questions)} questions to exam: {exam_name}")
                    else:
                        save_exam(exam_name, all_questions)
                        st.success(f"✅ Created exam: {exam_name} with {len(all_questions)} questions")
                    
                    # Show summary
                    st.markdown("### 📊 Parsing Summary")
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Total Questions", len(all_questions))
                    with col2:
                        st.metric("PDFs Processed", len(uploaded_files))
                    with col3:
                        image_count = sum(len(q.get("images", [])) for q in all_questions)
                        st.metric("Images Extracted", image_count)
                    
                    # Question type breakdown
                    type_counts = {}
                    for q in all_questions:
                        q_type = q.get("question_type", "unknown")
                        type_counts[q_type] = type_counts.get(q_type, 0) + 1
                    
                    st.markdown("**Question Types:**")
                    for q_type, count in type_counts.items():
                        st.write(f"- {q_type}: {count}")
                    
                except Exception as e:
                    st.error(f"Error parsing PDFs: {str(e)}")
                    import traceback
                    st.code(traceback.format_exc())


def take_exam_page():
    """Page for taking an exam - displays 100 questions per page."""
    exam_name = st.session_state.selected_exam
    questions = st.session_state.exam_questions
    
    if not questions:
        st.error("No questions found in this exam")
        if st.button("⬅️ Back to Home"):
            st.session_state.current_page = "home"
            st.rerun()
        return
    
    # Header
    col1, col2 = st.columns([3, 1])
    with col1:
        st.title(f"📝 {exam_name}")
    with col2:
        if st.button("🏠 Exit to Home"):
            st.session_state.current_page = "home"
            st.rerun()
    
    # Check if exam is submitted
    if st.session_state.exam_submitted:
        display_exam_results(exam_name, questions)
        return
    
    # Calculate pagination
    questions_per_page = st.session_state.questions_per_page
    total_pages = (len(questions) + questions_per_page - 1) // questions_per_page
    current_page = st.session_state.current_page_num
    
    # Ensure current page is valid
    if current_page >= total_pages:
        current_page = 0
        st.session_state.current_page_num = 0
    
    # Calculate question range for current page
    start_idx = current_page * questions_per_page
    end_idx = min(start_idx + questions_per_page, len(questions))
    current_questions = questions[start_idx:end_idx]
    
    # Progress indicator
    answered = len(st.session_state.user_answers)
    progress = answered / len(questions) if len(questions) > 0 else 0
    st.progress(progress)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Questions", f"{start_idx + 1}-{end_idx} of {len(questions)}")
    with col2:
        st.metric("Page", f"{current_page + 1} / {total_pages}")
    with col3:
        st.metric("Answered", f"{answered} / {len(questions)}")
    
    st.markdown("---")
    
    # Display all questions on current page
    for idx, question in enumerate(current_questions):
        actual_idx = start_idx + idx
        display_question(question, actual_idx)
    
    # Spacer to push navigation to bottom
    st.markdown("<br><br>", unsafe_allow_html=True)

    # Navigation and submit buttons - aligned to bottom
    st.markdown("---")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if current_page > 0:
            if st.button("⬅️ Previous Page", use_container_width=True):
                st.session_state.current_page_num -= 1
                st.rerun()

    with col2:
        if current_page < total_pages - 1:
            if st.button("Next Page ➡️", use_container_width=True):
                st.session_state.current_page_num += 1
                st.rerun()

    with col3:
        # Page selector
        page_options = list(range(1, total_pages + 1))
        selected_page = st.selectbox(
            "Jump to page:",
            page_options,
            index=current_page,
            key=f"page_selector_{current_page}"  # Unique key to force update
        )
        if selected_page - 1 != current_page:
            st.session_state.current_page_num = selected_page - 1
            st.rerun()

    with col4:
        if st.button("✅ Submit Exam", type="primary", use_container_width=True):
            st.session_state.exam_submitted = True
            st.rerun()

    # Additional bottom spacing
    st.markdown("<br>", unsafe_allow_html=True)


def display_question(question: Dict[str, Any], index: int):
    """Display a single question with appropriate input widget."""
    st.markdown("---")
    
    # Question text - clean formatting
    question_text = question["question"]
    # Remove case study formatting and headers
    question_text = re.sub(r'HOTSPOT.*?(?=Question|\Z)', '', question_text, flags=re.IGNORECASE | re.DOTALL)
    question_text = re.sub(r'Case study.*?(?=Question|\Z)', '', question_text, flags=re.IGNORECASE | re.DOTALL)
    question_text = re.sub(r'This is a case study\..*?(?=Question|\Z)', '', question_text, flags=re.IGNORECASE | re.DOTALL)
    question_text = re.sub(r'Microsoft Certified.*?(?:Question Bank|Study Materials).*?(?:\(|-|\d+ of \d+|$)', '', question_text, flags=re.IGNORECASE | re.DOTALL)

    st.markdown(f"### Question {index + 1}")
    st.markdown(question_text.strip())
    
    # Display images if any
    images = question.get("images", [])
    if images:
        st.info("ℹ️ **Note:** Images below may contain tables, diagrams, or answer grids (HOTSPOT questions)")
        st.markdown("**Related Images:**")
        cols = st.columns(min(len(images), 3))
        for idx, img_name in enumerate(images):
            with cols[idx % 3]:
                img_path = os.path.join(get_images_dir(st.session_state.selected_exam), img_name)
                if os.path.exists(img_path):
                    st.image(img_path, use_container_width=True, caption=f"Image {idx + 1}")
    
    # Get question type
    q_type = question.get("question_type", "multiple_choice_single")
    question_id = question["question_id"]
    choices = question.get("choices", {})
    
    # Clean choices to remove inline explanations and trailing colons
    clean_choices = {}
    for key, value in choices.items():
        # Remove explanations that start with "Incorrect because" or after first colon
        clean_text = value.split("Incorrect because")[0].strip()
        clean_text = clean_text.split("Correct because")[0].strip()
        # If text still has a colon, it might be "Option: Explanation" format
        if ": " in clean_text:
            clean_text = clean_text.split(": ")[0].strip()
        # Remove trailing colons
        clean_text = clean_text.rstrip(':').strip()
        clean_choices[key] = clean_text if clean_text else value
    
    # For drag-and-drop and image_selection (hotspot), use text input
    if q_type == "drag_and_drop" or q_type == "image_selection":
        st.info("💡 **Study Question:** Review the question and images, then write your answer below.")
        current_answer = st.session_state.user_answers.get(question_id, "")
        answer = st.text_area(
            "Your answer:",
            value=current_answer,
            height=150,
            key=f"q_{question_id}",
            help="Write your complete answer here. You can check the correct answer using the 'Show Answer' button below."
        )
        
        if answer:
            st.session_state.user_answers[question_id] = answer
    
    # Display appropriate input widget for other question types
    elif q_type == "multiple_choice_single" or q_type == "yes_no":
        options = list(clean_choices.keys())
        
        # Get current answer
        current_answer = st.session_state.user_answers.get(question_id, None)
        default_index = options.index(current_answer) if current_answer in options else 0
        
        answer = st.radio(
            "Select your answer:",
            options=options,
            format_func=lambda x: f"{x}. {clean_choices[x]}",
            index=default_index if current_answer else None,
            key=f"q_{question_id}"
        )
        
        if answer:
            st.session_state.user_answers[question_id] = answer
    
    elif q_type == "multiple_choice_multiple":
        options = list(clean_choices.keys())
        
        # Get current answer
        current_answer = st.session_state.user_answers.get(question_id, [])
        if isinstance(current_answer, str):
            current_answer = [a.strip() for a in current_answer.split(",")]
        
        answer = st.multiselect(
            "Select all that apply:",
            options=options,
            format_func=lambda x: f"{x}. {clean_choices[x]}",
            default=current_answer,
            key=f"q_{question_id}"
        )
        
        if answer:
            st.session_state.user_answers[question_id] = ",".join(sorted(answer))
    
    elif q_type == "input_text":
        current_answer = st.session_state.user_answers.get(question_id, "")
        answer = st.text_area(
            "Your answer:",
            value=current_answer,
            key=f"q_{question_id}"
        )
        
        if answer:
            st.session_state.user_answers[question_id] = answer
    
    else:
        # Default to radio for unknown types
        options = list(clean_choices.keys())
        current_answer = st.session_state.user_answers.get(question_id, None)
        
        answer = st.radio(
            "Select your answer:",
            options=options,
            format_func=lambda x: f"{x}. {clean_choices[x]}",
            index=options.index(current_answer) if current_answer in options else 0,
            key=f"q_{question_id}"
        )
        
        if answer:
            st.session_state.user_answers[question_id] = answer
    
    # Show Answer button (optional during exam)
    st.markdown("---")
    if st.button("💡 Show Answer", key=f"show_answer_{question_id}"):
        correct_answer = question.get("web_recommended_answer") or question.get("pdf_answer") or question.get("ai_recommended_answer")
        
        if correct_answer:
            st.success(f"**Correct Answer:** {correct_answer}")
            
            # Show explanations if available
            if question.get("web_explanation"):
                with st.expander("📖 Web Explanation"):
                    st.info(question["web_explanation"])
            
            if question.get("ai_explanation"):
                with st.expander("🤖 AI Explanation"):
                    st.info(question["ai_explanation"])
        else:
            st.warning("No answer available for this question")


def display_exam_results(exam_name: str, questions: List[Dict[str, Any]]):
    """Display exam results and detailed review."""
    st.markdown("---")
    st.title("📊 Exam Results")
    
    # Calculate score
    score = 0
    total = len(questions)
    details = []
    
    for question in questions:
        question_id = question["question_id"]
        user_answer = st.session_state.user_answers.get(question_id, None)
        correct_answer = question.get("web_recommended_answer") or question.get("pdf_answer")
        
        # Normalize answers for comparison
        if isinstance(user_answer, str):
            user_answer_normalized = user_answer.replace(" ", "").upper()
        else:
            user_answer_normalized = str(user_answer)
        
        if isinstance(correct_answer, str):
            correct_answer_normalized = correct_answer.replace(" ", "").upper()
        else:
            correct_answer_normalized = str(correct_answer)
        
        is_correct = user_answer_normalized == correct_answer_normalized
        if is_correct:
            score += 1
        
        details.append({
            "question_id": question_id,
            "question": question["question"],
            "user_answer": user_answer,
            "correct_answer": correct_answer,
            "is_correct": is_correct,
            "web_explanation": question.get("web_explanation", ""),
            "ai_explanation": question.get("ai_explanation", "")
        })
    
    # Display score
    percentage = (score / total * 100) if total > 0 else 0
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Score", f"{score} / {total}")
    with col2:
        st.metric("Percentage", f"{percentage:.1f}%")
    with col3:
        status = "✅ PASS" if percentage >= 70 else "❌ FAIL"
        st.metric("Status", status)
    
    # Save results
    save_exam_result(exam_name, score, total, st.session_state.user_answers, details)
    
    # Detailed review
    st.markdown("---")
    st.subheader("📝 Detailed Review")
    
    for idx, detail in enumerate(details):
        with st.expander(f"Question {idx + 1} - {'✅ Correct' if detail['is_correct'] else '❌ Incorrect'}"):
            st.markdown(f"**Question:** {detail['question']}")
            st.markdown(f"**Your Answer:** {detail['user_answer'] or 'Not answered'}")
            st.markdown(f"**Correct Answer:** {detail['correct_answer']}")
            
            if detail['web_explanation']:
                st.markdown("**Web Explanation:**")
                st.info(detail['web_explanation'])
            
            if detail['ai_explanation']:
                st.markdown("**AI Explanation:**")
                st.info(detail['ai_explanation'])
    
    # Action buttons
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🏠 Back to Home", use_container_width=True):
            st.session_state.current_page = "home"
            st.session_state.exam_submitted = False
            st.session_state.user_answers = {}
            st.rerun()
    
    with col2:
        if st.button("🔄 Retake Exam", use_container_width=True):
            st.session_state.exam_submitted = False
            st.session_state.user_answers = {}
            st.session_state.current_question_index = 0
            st.rerun()


def edit_exam_page():
    """Page for editing exam questions."""
    exam_name = st.session_state.selected_exam
    
    st.title(f"✏️ Edit Exam: {exam_name}")
    
    if st.button("⬅️ Back to Home"):
        st.session_state.current_page = "home"
        st.rerun()
    
    st.markdown("---")
    
    # Load questions
    questions = load_exam(exam_name)
    
    if not questions:
        st.warning("No questions found in this exam")
        return
    
    st.info(f"Total Questions: {len(questions)}")
    
    # Question selector
    question_ids = [q["question_id"] for q in questions]
    selected_id = st.selectbox(
        "Select Question to Edit",
        question_ids,
        format_func=lambda x: f"Question {x}"
    )
    
    # Find selected question
    question = next((q for q in questions if q["question_id"] == selected_id), None)
    
    if question:
        st.markdown("---")
        st.subheader(f"Edit Question {selected_id}")
        
        # Editable fields
        with st.form(f"edit_form_{selected_id}"):
            question_text = st.text_area("Question Text", value=question["question"], height=150)
            
            st.markdown("**Choices:**")
            choices = question.get("choices", {})
            new_choices = {}
            for letter in sorted(choices.keys()):
                new_choices[letter] = st.text_input(f"Choice {letter}", value=choices[letter])
            
            col1, col2, col3 = st.columns(3)
            with col1:
                pdf_answer = st.text_input("PDF Answer", value=question.get("pdf_answer", ""))
            with col2:
                web_answer = st.text_input("Web Recommended", value=question.get("web_recommended_answer", ""))
            with col3:
                ai_answer = st.text_input("AI Recommended", value=question.get("ai_recommended_answer", ""))
            
            web_explanation = st.text_area("Web Explanation", value=question.get("web_explanation", ""), height=100)
            ai_explanation = st.text_area("AI Explanation", value=question.get("ai_explanation", ""), height=100)
            
            # Submit button
            if st.form_submit_button("💾 Save Changes", type="primary"):
                # Update question
                question["question"] = question_text
                question["choices"] = new_choices
                question["pdf_answer"] = pdf_answer
                question["web_recommended_answer"] = web_answer
                question["ai_recommended_answer"] = ai_answer
                question["web_explanation"] = web_explanation
                question["ai_explanation"] = ai_explanation
                
                # Save to file
                if update_exam_question(exam_name, selected_id, question):
                    st.success("✅ Question updated successfully!")
                    st.rerun()
                else:
                    st.error("Failed to update question")


def view_results_page():
    """Page for viewing exam attempt history."""
    exam_name = st.session_state.selected_exam
    
    st.title(f"📊 Results: {exam_name}")
    
    if st.button("⬅️ Back to Home"):
        st.session_state.current_page = "home"
        st.rerun()
    
    st.markdown("---")
    
    # Load results
    results = load_exam_results(exam_name)
    
    if not results:
        st.info("No exam attempts found")
        return
    
    # Display results summary
    stats = get_exam_stats(exam_name)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Attempts", stats.get("total_attempts", 0))
    with col2:
        st.metric("Average Score", f"{stats.get('average_score', 0):.1f}%")
    with col3:
        st.metric("Best Score", f"{stats.get('best_score', 0):.1f}%")
    
    st.markdown("---")
    
    # Display attempts
    st.subheader("Attempt History")
    
    for idx, result in enumerate(results):
        with st.expander(f"Attempt {idx + 1} - {result['timestamp']} - {result['percentage']:.1f}%"):
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Score", f"{result['score']} / {result['total']}")
            with col2:
                st.metric("Percentage", f"{result['percentage']:.1f}%")
            with col3:
                status = "✅ PASS" if result['percentage'] >= 70 else "❌ FAIL"
                st.metric("Status", status)
            
            # Show detailed breakdown if available
            if "details" in result:
                st.markdown("**Question Breakdown:**")
                correct_count = sum(1 for d in result["details"] if d.get("is_correct"))
                st.write(f"Correct: {correct_count} | Incorrect: {result['total'] - correct_count}")


# Main application routing
def main():
    """Main application entry point."""
    # Check password first
    if not check_password():
        return
    
    initialize_session_state()
    
    # Sidebar
    with st.sidebar:
        st.title("🎓 Exam Manager")
        st.markdown("---")
        
        # Navigation
        if st.session_state.current_page != "home":
            if st.button("🏠 Home", use_container_width=True):
                st.session_state.current_page = "home"
                st.rerun()
        
        st.markdown("---")
        
        # Display current exam info if selected
        if st.session_state.selected_exam:
            st.markdown("**Current Exam:**")
            st.info(st.session_state.selected_exam)
            
            stats = get_exam_stats(st.session_state.selected_exam)
            st.caption(f"{stats['total_questions']} questions")
    
    # Route to appropriate page
    if st.session_state.current_page == "home":
        home_page()
    elif st.session_state.current_page == "create_exam":
        create_exam_page()
    elif st.session_state.current_page == "take_exam":
        take_exam_page()
    elif st.session_state.current_page == "edit_exam":
        edit_exam_page()
    elif st.session_state.current_page == "view_results":
        view_results_page()
    else:
        home_page()


if __name__ == "__main__":
    main()
