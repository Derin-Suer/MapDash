"""
Name: Derin
Date: 03/05/2026

---MapDash---
This program is a quiz game that allows users to select a difficulty level (easy, medium, or difficult) and then answers questions from a database. The questions are randomly selected based on the chosen difficulty level. The user can continue playing until they choose to exit the game.
"""

#IMPORTS
import sqlite3
import random

#DB CONNECTION
connection = sqlite3.connect('questions.db')
cursor = connection.cursor()

#MAIN LOGIC
high_score = 0

print("Welcome to MapDash Quiz Game!")
print("Test your knowledge with questions from various categories and difficulty levels.")
print("FYI: write your answer out in letters, not numbers. For example, write 'twenty' instead of '20'. Unless stated otherwise\n")
questions_done = [] #all questions that have been asked in the current session

while True:
    score = 0
    
    #DIFFICULTY SELECTION
    while True:
        difficulty = input("Select difficulty (e, m, d): ").lower().strip()
        if difficulty in ['e', 'm', 'd']:
            break
        print("Invalid difficulty. Please select e for easy, m for medium, or d for difficult.")

    #QUESTION SELECTION
    for _ in range(10): #ask 10 questions   
        cursor.execute("SELECT id FROM questions WHERE difficulty = ?", (difficulty,))
        question_ids = [row[0] for row in cursor.fetchall() if row[0] not in questions_done]

        if not question_ids:
            print("No more questions available for this difficulty level.")
            option = input("Do you want to reset question bank for this difficulty? (y/n): ").lower().strip()
            if option == 'y':
                questions_done.clear()
            break
        question_id = random.choice(question_ids)
        questions_done.append(question_id)

        cursor.execute("SELECT question, answer FROM questions WHERE id = ?", (question_id,))
        question, answer = cursor.fetchone()
        answers = answer.split("|")
        user_answer = input(f"{question} ").strip().lower()
        if user_answer in [a.strip().lower() for a in answers]:
            print("Correct!")
            score += 1
        else:
            print(f"Wrong! The correct answer is: {answer}")

    if score > high_score:
        high_score = score
    print(f"Your score: {score}")
    print(f"High score: {high_score}")

    print()

    play_again = input("Do you want to play again? (y/n): ").lower().strip()
    if play_again != 'y':
        break