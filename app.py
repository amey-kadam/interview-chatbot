from flask import Flask, render_template, request, jsonify
import google.generativeai as genai
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)

genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
model = genai.GenerativeModel('gemini-1.5-flash')



interview_context = {}
rounds = [
    "core fundamentals",
    "data structures and algorithms",
    "libraries or frameworks",
    "object-oriented programming",
    "database interaction",
    "system design and problem solving",
    "company specific questions"
]

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/start_interview', methods=['POST'])
def start_interview():
    global interview_context
    interview_context = {
        'job_role': request.json['job_role'],
        'company_name': request.json['company_name'],
        'ctc': request.json['ctc'],
        'experience_level': request.json['experience_level'],
        'current_round': 0,
        'questions_asked': 0
    }
    
    return start_next_round()

@app.route('/chat', methods=['POST'])
def chat():
    user_input = request.json['message']
    
    interview_context['questions_asked'] += 1
    if interview_context['questions_asked'] >= 5:
        interview_context['current_round'] += 1
        interview_context['questions_asked'] = 0
        if interview_context['current_round'] >= len(rounds):
            return jsonify({'response': "Thank you for completing all rounds of the interview. Do you have any questions for me?", 'interview_completed': True})
        else:
            return start_next_round()
    
    difficulty = get_difficulty(interview_context['experience_level'])
    
    prompt = f"""You are an experienced interviewer at {interview_context['company_name']} conducting a technical round focused on {rounds[interview_context['current_round']]}. 

Your task is to provide a standalone question about {rounds[interview_context['current_round']]} without any preamble or request for previous responses.

Generate a question that:
1. Explores an aspect of {rounds[interview_context['current_round']]}
2. Is appropriate for a {difficulty} difficulty level
3. Does not reference or depend on any previous questions or answers

Format your response as follows:

[Question]
(Your new question here)

Important:
- Do not include any feedback or commentary
- Do not ask for or mention any previous responses
- Ensure the question is self-contained and can be answered independently
- Vary your question types (e.g., conceptual, practical, problem-solving)
- Keep the tone professional and direct"""

    response = model.generate_content(prompt)
    
    response_text = response.text.replace("**", "<strong>").replace("*", "</strong>")
    
    return jsonify({'response': response_text})

def start_next_round():
    difficulty = get_difficulty(interview_context['experience_level'])
    
    prompt = f"""You are an interviewer for {interview_context['company_name']} conducting a technical interview for the role of {interview_context['job_role']}.

1. Briefly introduce the new round focused on {rounds[interview_context['current_round']]} (1-2 sentences).
2. Ask the first question for this round that:
   - Is related to {rounds[interview_context['current_round']]}
   - Matches a {difficulty} difficulty level for a candidate with {interview_context['experience_level']} experience

Format your response as follows:

[Introduction]
(Your brief introduction to the round)

[Question]
(Your first question for this round)

Important:
- Keep the introduction concise
- Don't mention the CTC or repeat other interview details
- Avoid phrases like "Let's begin with" or "Our first question is"
- Keep the tone professional but conversational"""

    response = model.generate_content(prompt)
    
    response_text = response.text.replace("**", "<strong>").replace("*", "</strong>")
    
    return jsonify({'response': response_text, 'new_round': rounds[interview_context['current_round']]})

def get_difficulty(experience_level):
    if experience_level == "entry level":
        return "easy"
    elif experience_level == "mid level":
        return "medium"
    else:  
        return "hard"

if __name__ == '__main__':
    app.run(debug=True)