from flask import Flask, render_template, request, jsonify, session
import sqlite3
import random
import os

app = Flask(__name__)
app.secret_key = os.urandom(24) 


QUESTIONS_PER_ROUND = 10

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH  = os.path.join(BASE_DIR, "questions.db")


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


@app.route("/")
def hello_world():
    session.setdefault('high_score', 0)
    session.setdefault('questions_done', [])
    return render_template("index.html")


@app.route('/api/start', methods=['POST'])
def start_game():
    data = request.get_json()
    difficulty = data.get('difficulty', '').lower().strip()
 
    if difficulty not in ['e', 'm', 'd']:
        return jsonify({'error': 'Invalid difficulty'}), 400
 
    session['difficulty'] = difficulty
    session['score'] = 0
    session['question_number'] = 0

    session.setdefault('questions_done', [])
 
    return jsonify({'status': 'started', 'total': QUESTIONS_PER_ROUND})
 
 

@app.route('/api/question', methods=['GET'])
def get_question():
    difficulty = session.get('difficulty')
    q_number = session.get('question_number', 0)
    questions_done = session.get('questions_done', [])
 
    if q_number >= QUESTIONS_PER_ROUND:
        return jsonify({'status': 'round_over', 'score': session.get('score', 0)})
 
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM questions WHERE difficulty = ?", (difficulty,))
    all_ids = [row['id'] for row in cursor.fetchall()]
    available_ids = [i for i in all_ids if i not in questions_done]
 
    if not available_ids:
        conn.close()
        return jsonify({
            'status': 'no_questions',
            'score': session.get('score', 0),
            'message': 'No more questions available for this difficulty!'
        })
 
    question_id = random.choice(available_ids)
    cursor.execute("SELECT id, question FROM questions WHERE id = ?", (question_id,))
    row = cursor.fetchone()
    conn.close()
 
    # Store current question id in session (don't reveal answer)
    session['current_question_id'] = question_id
    session['question_number'] = q_number + 1
 
    return jsonify({
        'status': 'question',
        'question': row['question'],
        'number': session['question_number'],
        'total': QUESTIONS_PER_ROUND
    })
 

 
@app.route('/api/answer', methods=['POST'])
def check_answer():
    """Check the user's answer and update score."""
    data = request.get_json()
    user_answer = data.get('answer', '').strip().lower()
 
    question_id = session.get('current_question_id')
    if question_id is None:
        return jsonify({'error': 'No active question'}), 400
 
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT answer FROM questions WHERE id = ?", (question_id,))
    row = cursor.fetchone()
    conn.close()
 
    if row is None:
        return jsonify({'error': 'Question not found'}), 404
 
    correct_answers = [a.strip().lower() for a in row['answer'].split('|')]
    is_correct = user_answer in correct_answers
 
    # Update score and mark question as done
    if is_correct:
        session['score'] = session.get('score', 0) + 1
 
    questions_done = session.get('questions_done', [])
    questions_done.append(question_id)
    session['questions_done'] = questions_done
    session['current_question_id'] = None
 
    # Check if round is over
    round_over = session.get('question_number', 0) >= QUESTIONS_PER_ROUND
    score = session.get('score', 0)
 
    if round_over:
        high_score = session.get('high_score', 0)
        if score > high_score:
            session['high_score'] = score
            high_score = score
        return jsonify({
            'correct': is_correct,
            'correct_answer': row['answer'],
            'score': score,
            'high_score': high_score,
            'round_over': True
        })
 
    return jsonify({
        'correct': is_correct,
        'correct_answer': row['answer'],
        'score': score,
        'round_over': False
    })
 
 
@app.route('/api/reset_bank', methods=['POST'])
def reset_bank():
    """Clear the questions_done list so all questions become available again."""
    session['questions_done'] = []
    return jsonify({'status': 'reset'})
 
 
@app.route('/api/state', methods=['GET'])
def get_state():
    """Return current session state (score, high score, etc.)."""
    return jsonify({
        'high_score': session.get('high_score', 0),
        'score': session.get('score', 0),
        'questions_done_count': len(session.get('questions_done', []))
    })
 

if __name__ == "__main__":
    app.run(
        debug=False,
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000))
    )
