# 📚 Multi-Exam Management System

A comprehensive Streamlit web application for managing and taking ExamTopics-style certification exams. Upload PDF files, automatically parse questions with images, take practice exams, and track your progress over time.

## ✨ Features

### 🎯 Core Functionality
- **Multi-Exam Management**: Create and manage multiple exams (e.g., AZ-104, AZ-305, AZ-700)
- **PDF Parsing**: Automatically extract questions, choices, answers, and images from ExamTopics-style PDFs
- **Multi-Part Support**: Upload multiple PDF files for a single exam
- **Question Type Detection**: Automatically detects multiple choice, yes/no, drag-and-drop, and text input questions
- **Image Extraction**: Extracts and displays images associated with questions
- **Interactive Exam Taking**: One question per page with progress tracking
- **Instant Scoring**: Automatic grading with detailed explanations
- **Manual Editing**: Edit questions, answers, and explanations
- **Results History**: Track all exam attempts with detailed breakdowns

### 📊 Question Types Supported
- Multiple choice (single answer)
- Multiple choice (multiple answers)
- Yes/No questions
- Image selection questions
- Drag and drop questions
- Text input questions

## 🚀 Installation

### Prerequisites
- Python 3.8 or higher
- pip package manager

### Setup Steps

1. **Clone or download this repository**

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Verify installation**
```bash
python -c "import streamlit; import fitz; print('All dependencies installed!')"
```

## 📖 Usage

### Starting the Application

Run the Streamlit app:
```bash
streamlit run app.py
```

The application will open in your default web browser at `http://localhost:8501`

### Creating an Exam

1. Click **"➕ Create New Exam"**
2. Enter an exam name (e.g., "Azure Administrator AZ-104")
3. Upload one or more PDF files
4. Click **"🔄 Parse and Save Exam"**
5. Wait for parsing to complete (may take a few minutes)
6. Review the parsing summary

### Taking an Exam

1. From the home page, click **"📝 Take Exam"** for your chosen exam
2. Answer questions one at a time
3. Use **"Next ➡️"** and **"⬅️ Previous"** to navigate
4. **Optional:** Click **"💡 Show Answer"** to reveal the correct answer and explanations during practice
5. Click **"✅ Submit Exam"** when finished
6. Review your score and detailed explanations

### Editing Questions

1. Click **"✏️ Edit"** for an exam
2. Select a question to edit
3. Modify question text, choices, or answers
4. Click **"💾 Save Changes"**

### Viewing Results

1. Click **"📊 Results"** for an exam
2. View all attempt history
3. See statistics: average score, best score, total attempts

### Appending to Existing Exams

1. Click **"➕ Create New Exam"**
2. Check **"Append to existing exam"**
3. Select the exam to append to
4. Upload additional PDF files
5. New questions will be added to the existing exam

## 📁 Project Structure

```
exam-management/
├── app.py                      # Main Streamlit application
├── requirements.txt            # Python dependencies
├── README.md                   # This file
├── parser/
│   ├── __init__.py
│   ├── extract.py             # PDF extraction logic
│   └── parse_questions.py     # Question parsing logic
├── utils/
│   ├── __init__.py
│   └── storage.py             # Data persistence
├── data/                      # Created automatically
│   └── <exam_name>/
│       ├── exam.jsonl         # Exam questions
│       ├── images/            # Extracted images
│       └── results/           # Exam attempt results
└── pdfs/                      # Your PDF files (optional)
```

## 🔧 Data Model

Each question is stored with the following structure:

```json
{
    "question_id": 1,
    "source_pdf": "Part1.pdf",
    "page_number": 5,
    "question_type": "multiple_choice_single",
    "question": "What is the purpose of...",
    "choices": {
        "A": "Option A text",
        "B": "Option B text",
        "C": "Option C text",
        "D": "Option D text"
    },
    "pdf_answer": "A",
    "web_recommended_answer": "B",
    "ai_recommended_answer": "B",
    "web_explanation": "Explanation text...",
    "ai_explanation": "AI explanation text...",
    "images": ["Part1_page5_img1.png"],
    "user_answer": null
}
```

## 🎨 Features in Detail

### PDF Parsing

The parser automatically extracts:
- Question numbers and text
- Multiple choice options (A, B, C, D, etc.)
- Three types of answers:
  - **PDF Suggested Answer**: Original answer from PDF
  - **Web Recommended Answer**: Community-verified answer
  - **AI Recommended Answer**: AI-suggested answer
- Explanations from "Discussion Summary" and "AI Recommended Answer" sections
- All images with automatic page association

### Question Type Detection

The system intelligently detects:
- **Single Answer**: Standard multiple choice
- **Multiple Answer**: "Select two", "Choose all that apply"
- **Yes/No**: Binary questions
- **Image Selection**: Questions with images and few text options
- **Drag and Drop**: Questions with keywords like "match", "order", "arrange"
- **Text Input**: Fill-in-the-blank or free text responses

### Scoring System

- Answers are compared against the **Web Recommended Answer** (preferred)
- Falls back to **PDF Answer** if Web answer is not available
- Normalized comparison (case-insensitive, whitespace-removed)
- 70% passing threshold
- Detailed review shows correct/incorrect for each question

## 🛠️ Troubleshooting

### PDFs not parsing correctly?

- Ensure PDFs are from ExamTopics with standard formatting
- Check that questions start with "Question #" or "Question"
- Verify that choices are labeled A., B., C., D. (with periods)

### Images not displaying?

- Images are saved in `data/<exam_name>/images/`
- Check that the directory has write permissions
- Verify images were extracted during PDF parsing

### Application not starting?

```bash
# Check Python version
python --version  # Should be 3.8+

# Reinstall dependencies
pip install --upgrade -r requirements.txt

# Run with verbose output
streamlit run app.py --logger.level=debug
```

## 📝 Example Workflow

1. **Setup**: Install dependencies and start the app
2. **Create**: Upload "AZ-104-Part1.pdf" and "AZ-104-Part2.pdf"
3. **Name**: Enter "Azure Administrator AZ-104"
4. **Parse**: Wait for automatic parsing (extracts ~100-200 questions)
5. **Take**: Practice the exam, answer all questions
6. **Submit**: View your score and explanations
7. **Review**: Study incorrect answers with provided explanations
8. **Retake**: Attempt the exam again to improve your score
9. **Edit**: Fix any parsing errors manually if needed

## 🔒 Data Privacy

- All data is stored locally in the `data/` directory
- No data is sent to external servers
- Exam attempts and results remain on your machine
- You can delete exams at any time

## 🤝 Contributing

This is a complete, production-ready application. To extend it:

1. **Add new question types**: Modify `detect_question_type()` in `parse_questions.py`
2. **Enhance parsing**: Update regex patterns in `parse_questions.py`
3. **Add export formats**: Extend `export_results_to_csv()` in `storage.py`
4. **Improve UI**: Modify page functions in `app.py`

## 📄 License

This project is provided as-is for educational and personal use.

## 🙏 Acknowledgments

- Built with [Streamlit](https://streamlit.io/)
- PDF processing with [PyMuPDF](https://pymupdf.readthedocs.io/)
- Designed for ExamTopics-style certification exam PDFs

## 📧 Support

For issues or questions:
1. Check the troubleshooting section
2. Review the code comments
3. Verify your PDF format matches ExamTopics style

---

**Happy studying! 🎓**
