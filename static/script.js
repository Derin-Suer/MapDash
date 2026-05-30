
let waitingForNext = false;
let currentDifficulty = null;

function showScreen(id) {
    document.querySelectorAll('.screen').forEach(s => s.classList.remove('active'));
    document.getElementById('screen-' + id).classList.add('active');
}

async function fetchState() {
    const res = await fetch('/api/state');
    const data = await res.json();
    document.getElementById('score-display').textContent = data.score;
    document.getElementById('high-score-display').textContent = data.high_score;
}

async function startGame(difficulty) {
    currentDifficulty = difficulty;
    showScreen('loading');
    const res = await fetch('/api/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ difficulty })
    });
    if (!res.ok) { alert('Failed to start game'); return; }
    document.getElementById('score-display').textContent = '0';
    await loadQuestion();
}

async function loadQuestion() {
    showScreen('loading');
    const res = await fetch('/api/question');
    const data = await res.json();

    if (data.status === 'round_over') {
        showRoundOver(data.score);
        return;
    }

    if (data.status === 'no_questions') {
        showScreen('noquestions');
        return;
    }

    // Show question
    document.getElementById('q-counter').textContent = `Question ${data.number} / ${data.total}`;
    document.getElementById('progress-bar').style.width = ((data.number - 1) / data.total * 100) + '%';
    document.getElementById('question-text').textContent = data.question;
    document.getElementById('answer-input').value = '';
    document.getElementById('feedback').className = 'feedback';
    document.getElementById('feedback').textContent = '';
    document.getElementById('submit-btn').disabled = false;
    waitingForNext = false;

    showScreen('question');
    document.getElementById('answer-input').focus();

}

async function submitAnswer() {
    if (waitingForNext) {
        await loadQuestion();
        document.getElementById('submit-btn').textContent = 'Submit Answer →';
        return;
    }

    const answer = document.getElementById('answer-input').value.trim();
    if (!answer) return;

    document.getElementById('submit-btn').disabled = true;

    const res = await fetch('/api/answer', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ answer })
    });
    const data = await res.json();

    const fb = document.getElementById('feedback');
    if (data.correct) {
        fb.textContent = '✓ Correct!';
        fb.className = 'feedback correct visible';
    } else {
        fb.textContent = `✗ Wrong! The answer was: ${data.correct_answer}`;
        fb.className = 'feedback wrong visible';
    }

    document.getElementById('score-display').textContent = data.score;

    // Update progress bar
    const qText = document.getElementById('q-counter').textContent;
    const current = parseInt(qText.split(' ')[1]);
    const total = parseInt(qText.split(' ')[3]);
    document.getElementById('progress-bar').style.width = (current / total * 100) + '%';

    if (data.round_over) {
        setTimeout(() => showRoundOver(data.score, data.high_score), 900);
    } else {
        // Allow pressing submit again to advance
        waitingForNext = true;
        document.getElementById('submit-btn').textContent = 'Next Question →';
        document.getElementById('submit-btn').disabled = false;
    }
}

function showRoundOver(score, highScore) {
    document.getElementById('final-score').textContent = score;
    const newBest = document.getElementById('new-best');
    if (highScore !== undefined) {
        document.getElementById('high-score-display').textContent = highScore;
        newBest.style.display = (score === highScore && score > 0) ? 'block' : 'none';
    } else {
        newBest.style.display = 'none';
    }
    document.getElementById('submit-btn').textContent = 'Submit Answer';
    showScreen('roundover');
}

async function resetBank() {
    await fetch('/api/reset_bank', { method: 'POST' });
    goToDifficulty();
}

function goToDifficulty() {
    document.getElementById('submit-btn').textContent = 'Submit Answer';
    fetchState();
    showScreen('difficulty');
}

async function restartGame() {
    if (!confirm('Restart and go back to main menu? Your current score will be lost.')) return;
    await fetch('/api/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ difficulty: currentDifficulty })
    });
    document.getElementById('submit-btn').textContent = 'Submit Answer';
    waitingForNext = false;
    fetchState();          // reloads score + high score from server
    document.getElementById('score-display').textContent = '0';
    showScreen('difficulty');
}

// Press Enter to submit
document.getElementById('answer-input').addEventListener('keydown', e => {
    if (e.key === 'Enter') submitAnswer();
});

// Load initial state
fetchState();
