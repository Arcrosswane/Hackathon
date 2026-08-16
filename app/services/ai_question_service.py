import os
import json
import urllib.request
import urllib.error
from datetime import datetime
from app.models import db, AIQuestionGenerationLog, Question, SchoolClass, Subject, School
from app.services.question_bank_service import VALID_QUESTION_TYPES, VALID_DIFFICULTIES

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "AQ.Ab8RN6JGtaVgeEyfjolkx1dRSYZVeYhNn2wIKOwOVZdrWZ25ZA")

CANDIDATE_GEMINI_MODELS = [
    "gemini-2.5-flash",
    "gemini-1.5-flash-latest",
    "gemini-1.5-pro-latest",
    "gemini-pro"
]

def _call_gemini_api(payload, timeout=25):
    """
    Tries calling Gemini API across supported model names in sequence with automatic fallback.
    """
    last_error = None

    for model in CANDIDATE_GEMINI_MODELS:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={GEMINI_API_KEY}"
        try:
            json_data = json.dumps(payload).encode('utf-8')
            req = urllib.request.Request(
                url,
                data=json_data,
                headers={'Content-Type': 'application/json'}
            )
            with urllib.request.urlopen(req, timeout=timeout) as response:
                resp_body = response.read().decode('utf-8')
                return json.loads(resp_body)
        except urllib.error.HTTPError as e:
            err_body = e.read().decode('utf-8') if e.fp else str(e)
            if e.code == 404:
                last_error = f"Model {model} 404: {err_body[:100]}"
                continue # Fallback to next model
            raise ValueError(f"AI Generation Service Error (HTTP {e.code}): {err_body[:150]}")
        except Exception as e:
            last_error = str(e)
            continue

    raise ValueError(f"AI Generation Service Error across all Gemini models: {last_error}")


def generate_ai_questions(class_name, subject_name, chapters, difficulty="MEDIUM", num_questions=5, question_types=None, teacher_instructions=None, user_id=None, class_id=None, subject_id=None):
    """
    Calls Gemini API with automatic model fallback to generate structured candidate questions.
    Returns: list of validated question dicts.
    """
    if not class_name or not subject_name:
        raise ValueError("Class name and Subject name are required for AI generation.")

    num_q = max(1, min(int(num_questions or 5), 25)) # Clamp 1 to 25 questions
    q_types_str = ", ".join(question_types) if isinstance(question_types, list) else (question_types or "MCQ, SHORT_ANSWER")
    chapters_str = ", ".join(chapters) if isinstance(chapters, list) else (chapters or "General Topics")

    prompt = f"""
You are an expert school educator and question paper creator.
Generate exactly {num_q} high-quality academic questions for:
- Class: Grade {class_name}
- Subject: {subject_name}
- Chapter(s)/Topic(s): {chapters_str}
- Requested Difficulty: {difficulty}
- Allowed Question Types: {q_types_str}
- Custom Teacher Instructions: {teacher_instructions or 'Follow standard NCERT and CBSE academic guidelines.'}

IMPORTANT: You MUST respond ONLY with a raw valid JSON object adhering strictly to the schema below.
DO NOT include markdown formatting (like ```json), HTML, or extra text.

JSON Schema:
{{
  "questions": [
    {{
      "type": "MCQ", 
      "question": "Question text here...",
      "options": ["A. Option 1", "B. Option 2", "C. Option 3", "D. Option 4"],
      "correct_option": "A",
      "answer": "Correct answer summary...",
      "explanation": "Detailed explanation of the solution...",
      "marks": 1.0,
      "difficulty": "{difficulty.upper()}",
      "chapter": "{chapters_str}",
      "tags": "NCERT,Important"
    }}
  ]
}}

Rules:
1. For MCQ types, provide 4 distinct options in 'options' and set 'correct_option' to A, B, C, or D.
2. For SHORT_ANSWER / LONG_ANSWER / NUMERICAL types, set 'options' to [], 'correct_option' to "", and provide a clear model answer in 'answer'.
3. Set appropriate marks (1m for MCQ, 2m-3m for Short Answer, 5m for Long Answer).
4. Ensure question difficulty matches '{difficulty}'.
"""

    payload = {
        "contents": [
            {
                "parts": [
                    {"text": prompt}
                ]
            }
        ],
        "generationConfig": {
            "temperature": 0.7,
            "responseMimeType": "application/json"
        }
    }

    try:
        res_data = _call_gemini_api(payload, timeout=25)

        candidates = res_data.get('candidates', [])
        if not candidates:
            _log_ai_generation(user_id, class_id, subject_id, chapters_str, difficulty, q_types_str, prompt, "FAILED", 0)
            raise ValueError("AI Service returned no response candidates.")

        raw_text = candidates[0]['content']['parts'][0]['text']
        
        # Clean potential markdown wrapping if returned
        clean_text = raw_text.strip()
        if clean_text.startswith("```json"):
            clean_text = clean_text[7:]
        if clean_text.startswith("```"):
            clean_text = clean_text[3:]
        if clean_text.endswith("```"):
            clean_text = clean_text[:-3]
        clean_text = clean_text.strip()

        parsed_json = json.loads(clean_text)
        questions_raw = parsed_json.get('questions', [])

        # Server-side validation of generated questions
        validated_questions = []
        for item in questions_raw:
            q_text = item.get('question', '').strip()
            if not q_text:
                continue

            q_type = str(item.get('type', 'MCQ')).upper().strip()
            if q_type not in VALID_QUESTION_TYPES:
                q_type = 'MCQ'

            q_diff = str(item.get('difficulty', difficulty)).upper().strip()
            if q_diff not in VALID_DIFFICULTIES:
                q_diff = 'MEDIUM'

            opts = item.get('options', [])
            opt_a = opts[0] if len(opts) > 0 else item.get('option_a', '')
            opt_b = opts[1] if len(opts) > 1 else item.get('option_b', '')
            opt_c = opts[2] if len(opts) > 2 else item.get('option_c', '')
            opt_d = opts[3] if len(opts) > 3 else item.get('option_d', '')

            corr = str(item.get('correct_option', 'A')).upper().strip()
            if corr not in ('A', 'B', 'C', 'D'):
                corr = 'A'

            validated_questions.append({
                'class_id': class_id,
                'subject_id': subject_id,
                'question_text': q_text,
                'question_type': q_type,
                'difficulty': q_diff,
                'marks': float(item.get('marks', 1.0)),
                'chapter': item.get('chapter', chapters_str),
                'topic': item.get('topic', ''),
                'option_a': opt_a,
                'option_b': opt_b,
                'option_c': opt_c,
                'option_d': opt_d,
                'correct_option': corr if q_type == 'MCQ' else '',
                'answer_text': item.get('answer', ''),
                'explanation': item.get('explanation', ''),
                'tags': item.get('tags', 'AI_GENERATED')
            })

        _log_ai_generation(user_id, class_id, subject_id, chapters_str, difficulty, q_types_str, prompt, "SUCCESS", len(validated_questions))
        return validated_questions

    except Exception as e:
        _log_ai_generation(user_id, class_id, subject_id, chapters_str, difficulty, q_types_str, prompt, "FAILED", 0)
        raise e


def improve_question_with_ai(question_id, improvement_instructions):
    """
    Asks Gemini AI to improve, clarify, or reformat an existing question according to teacher feedback using urllib.request.
    """
    q = Question.query.get(question_id)
    if not q:
        raise ValueError("Original question not found.")

    prompt = f"""
You are an expert school educator. Improve the following question based on teacher feedback:
- Original Question: "{q.question_text}"
- Question Type: {q.question_type}
- Current Difficulty: {q.difficulty}
- Marks: {q.marks}
- Teacher Improvement Request: "{improvement_instructions}"

Respond ONLY with a raw valid JSON object with the improved question details:
{{
  "question": "Improved question text...",
  "options": ["A. Option 1", "B. Option 2", "C. Option 3", "D. Option 4"],
  "correct_option": "A",
  "answer": "Model answer...",
  "explanation": "Solution explanation...",
  "difficulty": "{q.difficulty}"
}}
"""

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.7, "responseMimeType": "application/json"}
    }

    try:
        res_data = _call_gemini_api(payload, timeout=20)
        raw_text = res_data['candidates'][0]['content']['parts'][0]['text']
        clean_text = raw_text.strip().replace("```json", "").replace("```", "").strip()
        parsed = json.loads(clean_text)

        opts = parsed.get('options', [])
        return {
            'original_id': q.id,
            'question_text': parsed.get('question', q.question_text),
            'question_type': q.question_type,
            'difficulty': parsed.get('difficulty', q.difficulty),
            'marks': q.marks,
            'option_a': opts[0] if len(opts) > 0 else q.option_a,
            'option_b': opts[1] if len(opts) > 1 else q.option_b,
            'option_c': opts[2] if len(opts) > 2 else q.option_c,
            'option_d': opts[3] if len(opts) > 3 else q.option_d,
            'correct_option': parsed.get('correct_option', q.correct_option),
            'answer_text': parsed.get('answer', q.answer_text),
            'explanation': parsed.get('explanation', q.explanation)
        }
    except Exception as e:
        raise ValueError(f"AI Question Improvement failed: {str(e)}")


def convert_document_to_questions(raw_file_bytes, filename, class_id=None, subject_id=None, user_id=None):
    """
    Parses an uploaded PDF, Excel (.xlsx/.csv), or text document and uses Gemini AI to convert
    its contents into structured Question Bank items.
    """
    if not raw_file_bytes:
        raise ValueError("No file content uploaded.")

    file_text = ""
    fn_lower = filename.lower()

    if fn_lower.endswith('.csv') or fn_lower.endswith('.txt'):
        try:
            file_text = raw_file_bytes.decode('utf-8', errors='ignore')
        except Exception:
            file_text = str(raw_file_bytes)
    else:
        try:
            file_text = raw_file_bytes.decode('utf-8', errors='ignore')
        except Exception:
            file_text = "".join(chr(b) for b in raw_file_bytes if 32 <= b <= 126 or b in (10, 13, 9))

    if not file_text or len(file_text.strip()) < 10:
        raise ValueError("Could not extract readable text content from the uploaded document.")

    file_text = file_text[:4000]

    s_class = SchoolClass.query.get(class_id) if class_id else None
    subject = Subject.query.get(subject_id) if subject_id else None

    class_name = s_class.display_name if s_class else "General Grade"
    subject_name = subject.name if subject else "General Subject"

    prompt = f"""
You are an expert educational document parser.
Extract all questions, MCQs, short answers, options, and model answers from the following raw document content into a structured JSON array:

Document Name: {filename}
Target Class: {class_name}
Target Subject: {subject_name}

Raw Document Content:
\"\"\"
{file_text}
\"\"\"

Respond ONLY with a raw valid JSON object adhering strictly to the schema below.
DO NOT include markdown formatting, HTML, or extra text.

JSON Schema:
{{
  "questions": [
    {{
      "type": "MCQ", 
      "question": "Question statement extracted from document...",
      "options": ["A. Option 1", "B. Option 2", "C. Option 3", "D. Option 4"],
      "correct_option": "A",
      "answer": "Answer summary if present...",
      "explanation": "Explanation if present...",
      "marks": 1.0,
      "difficulty": "MEDIUM",
      "chapter": "Imported Document",
      "tags": "IMPORTED"
    }}
  ]
}}
"""

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.3, "responseMimeType": "application/json"}
    }

    try:
        res_data = _call_gemini_api(payload, timeout=30)
        candidates = res_data.get('candidates', [])
        if not candidates:
            raise ValueError("AI Document Converter returned no candidates.")

        raw_text = candidates[0]['content']['parts'][0]['text']
        clean_text = raw_text.strip().replace("```json", "").replace("```", "").strip()
        parsed = json.loads(clean_text)
        questions_raw = parsed.get('questions', [])

        validated = []
        for item in questions_raw:
            q_text = item.get('question', '').strip()
            if not q_text:
                continue

            q_type = str(item.get('type', 'MCQ')).upper().strip()
            if q_type not in VALID_QUESTION_TYPES:
                q_type = 'MCQ'

            opts = item.get('options', [])
            validated.append({
                'class_id': class_id,
                'subject_id': subject_id,
                'question_text': q_text,
                'question_type': q_type,
                'difficulty': str(item.get('difficulty', 'MEDIUM')).upper(),
                'marks': float(item.get('marks', 1.0)),
                'chapter': item.get('chapter', 'Imported Document'),
                'option_a': opts[0] if len(opts) > 0 else '',
                'option_b': opts[1] if len(opts) > 1 else '',
                'option_c': opts[2] if len(opts) > 2 else '',
                'option_d': opts[3] if len(opts) > 3 else '',
                'correct_option': str(item.get('correct_option', 'A')).upper() if q_type == 'MCQ' else '',
                'answer_text': item.get('answer', ''),
                'explanation': item.get('explanation', ''),
                'tags': 'IMPORTED,Converted'
            })

        _log_ai_generation(user_id, class_id, subject_id, "Document Import", "MEDIUM", "IMPORTED", prompt, "SUCCESS", len(validated))
        return validated

    except Exception as e:
        _log_ai_generation(user_id, class_id, subject_id, "Document Import", "MEDIUM", "IMPORTED", prompt, "FAILED", 0)
        raise ValueError(f"Document Question Converter failed: {str(e)}")


def _log_ai_generation(user_id, class_id, subject_id, chapters, difficulty, q_types, prompt, status, count):
    """Internal helper to log AI generation requests."""
    try:
        sch = School.query.first()
        school_id = sch.id if sch else 1
        log = AIQuestionGenerationLog(
            institute_id=school_id,
            requested_by_id=user_id,
            class_id=class_id,
            subject_id=subject_id,
            chapters=chapters[:250] if chapters else '',
            difficulty=difficulty,
            question_types=q_types[:250] if q_types else '',
            prompt_summary=prompt[:500] if prompt else '',
            response_status=status,
            questions_generated=count
        )
        db.session.add(log)
        db.session.commit()
    except Exception:
        pass
