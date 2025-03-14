import streamlit as st
import os
from openai import OpenAI
from dotenv import load_dotenv
from typing import Dict

# Load environment variables
load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

def get_questions():
    try:
        completion = client.chat.completions.create(
            model=os.getenv('GPT_MODEL'),
            messages=[
                {"role": "system", "content": "You are an expert technical interviewer for backend developer positions. Generate challenging but fair questions that assess both theoretical knowledge and practical experience."}, 
                {"role": "user", "content": "Generate 5 technical interview questions for a backend developer position, focusing on System Design, API Development, Database Management, Security, and Problem Solving. Return only a JSON array of question strings without any additional formatting or explanation."}
            ]
        )
        response_text = completion.choices[0].message.content.strip()
        try:
            import json
            questions = json.loads(response_text)
            if isinstance(questions, list) and len(questions) > 0:
                return questions
        except json.JSONDecodeError:
            import re
            array_match = re.search(r'\[.*\]', response_text, re.DOTALL)
            if array_match:
                try:
                    questions = json.loads(array_match.group())
                    if isinstance(questions, list) and len(questions) > 0:
                        return questions
                except:
                    pass
        return []
    except Exception as e:
        st.error(f"Error generating questions: {e}")
        return []



def analyze_response(text: str) -> Dict:
    if not text.strip():
        return {
            "technical_score": 0.0,
            "communication_score": 0.0,
            "feedback": "Please provide a response before submitting."
        }

    try:
        completion = client.chat.completions.create(
            model=os.getenv('GPT_MODEL'),
            messages=[
                {"role": "system", "content": "You are an expert technical interviewer evaluating a backend developer candidate's response. Provide constructive feedback that highlights both strengths and areas for improvement."}, 
                {"role": "user", "content": f"Evaluate this response to a backend development question:\n{text}\n\nProvide evaluation in JSON format with keys: technical_score (0-10), communication_score (0-10), and feedback (string)"}
            ]
        )
        
        response_text = completion.choices[0].message.content.strip()
        
        try:
            analysis = json.loads(response_text)
        except json.JSONDecodeError:
            import re
            scores = re.findall(r'(["\']?(?:technical|communication)_score["\']?)\s*:\s*(\d+(?:\.\d+)?)', response_text, re.I)
            feedback = re.search(r'["\']?feedback["\']?\s*:\s*["\']([^"]+)["\']', response_text)
            
            if scores and feedback:
                analysis = {
                    'technical_score': float(next(score[1] for score in scores if 'technical' in score[0].lower())),
                    'communication_score': float(next(score[1] for score in scores if 'communication' in score[0].lower())),
                    'feedback': feedback.group(1)
                }
            else:
                analysis = {
                    'technical_score': 0.0,
                    'communication_score': 0.0,
                    'feedback': 'Could not analyze response format. Please try rephrasing your answer.'
                }
        
        analysis['technical_score'] = max(0.0, min(10.0, float(analysis.get('technical_score', 0.0))))
        analysis['communication_score'] = max(0.0, min(10.0, float(analysis.get('communication_score', 0.0))))
        analysis['feedback'] = str(analysis.get('feedback', 'No feedback provided.'))
        
        return analysis
    except Exception as e:
        return {
            "technical_score": 0.0,
            "communication_score": 0.0,
            "feedback": f"An error occurred while analyzing your response. Please try again."
        }

def display_analysis(analysis, text):
    st.markdown("### Analysis Results")
    st.markdown("**Your Response:**")
    st.markdown(f"""<div style='padding: 1rem; border-left: 3px solid #1f77b4; margin: 1rem 0;'>
        {text}
    </div>""", unsafe_allow_html=True)
    st.markdown(f"**Technical Score:** {analysis['technical_score']}/10")
    st.markdown(f"**Communication Score:** {analysis['communication_score']}/10")
    st.markdown("**Feedback:**")
    st.markdown(f"""<div style='padding: 1rem; background-color: #ffffff; border: 1px solid #ddd; border-radius: 0.5rem; margin: 1rem 0;'>
        {analysis['feedback']}
    </div>""", unsafe_allow_html=True)
    
    if st.session_state.current_question_index < len(st.session_state.questions) - 1:
        st.session_state.current_question_index += 1
        st.rerun()
    else:
        display_final_assessment()

def display_final_assessment():
    if not st.session_state.responses:
        return
    
    total_technical = sum(float(response['analysis']['technical_score']) for response in st.session_state.responses)
    total_communication = sum(float(response['analysis']['communication_score']) for response in st.session_state.responses)
    
    avg_technical = total_technical / len(st.session_state.responses)
    avg_communication = total_communication / len(st.session_state.responses)
    avg_overall = (avg_technical + avg_communication) / 2
    
    passed = avg_overall >= 7.0
    
    st.markdown("---")
    st.markdown("## 📊 Final Assessment")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Technical Score", f"{avg_technical:.1f}/10")
    with col2:
        st.metric("Communication Score", f"{avg_communication:.1f}/10")
    with col3:
        st.metric("Overall Score", f"{avg_overall:.1f}/10")
    
    if passed:
        st.markdown(f"""<div style='background-color: #d4edda; color: #155724; padding: 1rem; border-radius: 0.5rem; margin: 1rem 0; text-align: center; font-size: 1.2rem;'>
            <strong>PASSED</strong> - Congratulations! You've successfully passed the interview with an overall score of {avg_overall:.1f}/10.
        </div>""", unsafe_allow_html=True)
    else:
        st.markdown(f"""<div style='background-color: #f8d7da; color: #721c24; padding: 1rem; border-radius: 0.5rem; margin: 1rem 0; text-align: center; font-size: 1.2rem;'>
            <strong>NOT PASSED</strong> - Thank you for your participation. Your overall score was {avg_overall:.1f}/10, which is below our threshold of 7.0/10.
        </div>""", unsafe_allow_html=True)
    
    st.success("🎉 Interview completed! Thank you for your participation.")

# Set up the page configuration
st.set_page_config(
    page_title="AI Technical Recruiter",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS
st.markdown("""
<style>
    .stTextArea textarea {font-size: 1rem !important; min-height: 200px !important;}
    .main .block-container {padding-top: 2rem;}
    .stProgress > div > div > div {height: 1rem;}
    .stButton > button {padding: 0.5rem 2rem; height: auto;}
    div[data-testid="stExpander"] {border: 1px solid #ddd; border-radius: 0.5rem; margin: 1rem 0;}
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'current_question_index' not in st.session_state:
    st.session_state.current_question_index = 0

if 'questions' not in st.session_state:
    st.session_state.questions = []

if 'responses' not in st.session_state:
    st.session_state.responses = []



# Main UI
st.title("🎯 AI Technical Recruiter")

# Fetch questions if not already loaded
if not st.session_state.questions:
    with st.spinner("Loading interview questions..."):
        st.session_state.questions = get_questions()
        if not st.session_state.questions:
            st.error("Failed to load questions. Please refresh the page to try again.")
            st.stop()

# Display current question
if st.session_state.questions:
    current_question = st.session_state.questions[st.session_state.current_question_index]
    st.header(f"Question {st.session_state.current_question_index + 1}/{len(st.session_state.questions)}")
    st.markdown(f"""<div style='background-color: #f0f2f6; padding: 1.5rem; border-radius: 0.5rem; margin: 1rem 0;'>
        {current_question}
    </div>""", unsafe_allow_html=True)

    # Text input option
    with st.container():
        st.markdown("### ⌨️ Text Response")
        text_response = st.text_area("Type your response here:", height=200)
        submitted = st.button("Submit Response", use_container_width=True)
        if submitted and text_response.strip():
            with st.spinner("Analyzing your response..."):
                analysis = analyze_response(text_response)
                st.session_state.responses.append({
                    'question': current_question,
                    'text': text_response,
                    'analysis': analysis
                })
                display_analysis(analysis, text_response)
        elif submitted:
            st.error("Please enter your response before submitting.")



# Display progress
st.markdown("### Progress")
st.progress((st.session_state.current_question_index + 1) / len(st.session_state.questions))

# Display previous responses
if st.session_state.responses:
    with st.expander("📝 Previous Responses"):
        for i, response in enumerate(st.session_state.responses):
            st.markdown(f"**Question {i + 1}:**")
            st.markdown(f"""<div style='background-color: #f0f2f6; padding: 1rem; border-radius: 0.5rem; margin-bottom: 1rem;'>
                {response['question']}
            </div>""", unsafe_allow_html=True)
            st.markdown("**Your Answer:**")
            st.markdown(f"""<div style='padding: 1rem; border-left: 3px solid #1f77b4; margin-bottom: 1rem;'>
                {response['text']}
            </div>""", unsafe_allow_html=True)
            st.markdown(f"**Technical Score:** {response['analysis']['technical_score']}/10")
            st