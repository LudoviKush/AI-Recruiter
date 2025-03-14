import streamlit as st
import requests
import json
import sounddevice as sd
import numpy as np
import scipy.io.wavfile as wav
import os

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
    
    # Automatically advance to next question after displaying analysis
    if st.session_state.current_question_index < len(st.session_state.questions) - 1:
        st.session_state.current_question_index += 1
        st.rerun()
    else:
        # Calculate final scores when all questions are answered
        display_final_assessment()

# Function to calculate average scores and display final assessment
def display_final_assessment():
    if not st.session_state.responses:
        return
    
    # Calculate average scores using Python (not relying on LLM)
    total_technical = 0
    total_communication = 0
    
    for response in st.session_state.responses:
        total_technical += float(response['analysis']['technical_score'])
        total_communication += float(response['analysis']['communication_score'])
    
    avg_technical = total_technical / len(st.session_state.responses)
    avg_communication = total_communication / len(st.session_state.responses)
    avg_overall = (avg_technical + avg_communication) / 2
    
    # Determine if candidate passed (threshold is 7/10)
    passed = avg_overall >= 7.0
    
    # Display final assessment with pass/fail status
    st.markdown("---")
    st.markdown("## 📊 Final Assessment")
    
    # Create columns for scores
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Technical Score", f"{avg_technical:.1f}/10")
    with col2:
        st.metric("Communication Score", f"{avg_communication:.1f}/10")
    with col3:
        st.metric("Overall Score", f"{avg_overall:.1f}/10")
    
    # Display pass/fail status with appropriate styling
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

# Custom CSS for better styling
st.markdown("""
<style>
    .stTextArea textarea {font-size: 1rem !important; min-height: 200px !important;}
    .main .block-container {padding-top: 2rem;}
    .stProgress > div > div > div {height: 1rem;}
    .stButton > button {padding: 0.5rem 2rem; height: auto;}
    div[data-testid="stExpander"] {border: 1px solid #ddd; border-radius: 0.5rem; margin: 1rem 0;}
</style>
""", unsafe_allow_html=True)

# Initialize session state variables
if 'current_question_index' not in st.session_state:
    st.session_state.current_question_index = 0

if 'questions' not in st.session_state:
    st.session_state.questions = []

if 'responses' not in st.session_state:
    st.session_state.responses = []

if 'recording' not in st.session_state:
    st.session_state.recording = False

if 'audio_data' not in st.session_state:
    st.session_state.audio_data = []

# Backend API URL
API_URL = "http://localhost:8000"

def fetch_questions():
    try:
        response = requests.get(f"{API_URL}/questions")
        if response.status_code == 200:
            st.session_state.questions = response.json()
            return True
        else:
            st.error(f"Failed to fetch questions: {response.text}")
            return False
    except requests.exceptions.RequestException as e:
        st.error(f"Error connecting to the backend: {str(e)}")
        return False

def record_audio():
    fs = 44100  # Sample rate
    duration = 30  # Recording duration in seconds
    st.session_state.recording = True
    st.session_state.audio_data = sd.rec(int(fs * duration), samplerate=fs, channels=1, dtype='float32')

def stop_recording():
    sd.stop()
    st.session_state.recording = False
    if len(st.session_state.audio_data) > 0:
        # Save the recorded audio
        wav.write('temp_recording.wav', 44100, st.session_state.audio_data)
        return True
    return False

def analyze_response(audio_file):
    try:
        files = {'audio': ('audio.wav', open(audio_file, 'rb'), 'audio/wav')}
        response = requests.post(f"{API_URL}/speech-to-text", files=files)
        if response.status_code == 200:
            text_response = response.json().get('text', '')
            analysis_response = requests.post(
                f"{API_URL}/analyze-response",
                json={"text": text_response}
            )
            if analysis_response.status_code == 200:
                return analysis_response.json(), text_response
    except Exception as e:
        st.error(f"Error analyzing response: {str(e)}")
    return None, None

# Main UI
st.title("🎯 AI Technical Recruiter")

# Fetch questions if not already loaded
if not st.session_state.questions:
    with st.spinner("Loading interview questions..."):
        if not fetch_questions():
            st.error("Failed to load questions. Please refresh the page to try again.")
            st.stop()

# Display current question
if st.session_state.questions:
    current_question = st.session_state.questions[st.session_state.current_question_index]
    st.header(f"Question {st.session_state.current_question_index + 1}/{len(st.session_state.questions)}")
    st.markdown(f"""<div style='background-color: #f0f2f6; padding: 1.5rem; border-radius: 0.5rem; margin: 1rem 0;'>
        {current_question}
    </div>""", unsafe_allow_html=True)

    # Create two main columns for recording and text input
    left_col, right_col = st.columns([1, 1])
    
    # Recording controls
    with left_col:
        st.markdown("### 🎤 Voice Response")
        if not st.session_state.recording:
            if st.button("Start Recording", use_container_width=True):
                record_audio()
        else:
            if st.button("⏹️ Stop Recording", use_container_width=True):
                if stop_recording():
                    with st.spinner("Analyzing your response..."):
                        analysis, text = analyze_response('temp_recording.wav')
                        if analysis and text:
                            st.session_state.responses.append({
                                'question': current_question,
                                'text': text,
                                'analysis': analysis
                            })
                            if os.path.exists('temp_recording.wav'):
                                os.remove('temp_recording.wav')
                            
                            display_analysis(analysis, text)

    # Text input option
    with right_col:
        st.markdown("### ⌨️ Text Response")
        text_response = st.text_area("Type your response here:", height=200)
        submitted = st.button("Submit Response", use_container_width=True)
        if submitted and text_response.strip():
            with st.spinner("Analyzing your response..."):
                try:
                    response = requests.post(
                        f"{API_URL}/analyze-response",
                        json={"text": text_response},
                        timeout=30  # Add timeout to prevent hanging
                    )
                    if response.status_code == 200:
                        analysis = response.json()
                        if isinstance(analysis, dict) and all(k in analysis for k in ['technical_score', 'communication_score', 'feedback']):
                            st.session_state.responses.append({
                                'question': current_question,
                                'text': text_response,
                                'analysis': analysis
                            })
                            display_analysis(analysis, text_response)
                        else:
                            st.error("Received invalid response format from server. Please try again.")
                    else:
                        error_msg = response.json().get('feedback', 'Failed to analyze response. Please try again.')
                        st.error(error_msg)
                except requests.exceptions.Timeout:
                    st.error("Request timed out. Please try again.")
                except requests.exceptions.RequestException as e:
                    st.error(f"Connection error: {str(e)}. Please try again.")
                except Exception as e:
                    st.error(f"An unexpected error occurred: {str(e)}. Please try again.")
        elif submitted:
            st.error("Please enter your response before submitting.")

    # Display recording status
    if st.session_state.recording:
        st.markdown("""<div style='color: #ff4b4b; padding: 1rem; text-align: center;'>
            🔴 Recording in progress...
        </div>""", unsafe_allow_html=True)

# Display progress with better styling
st.markdown("### Progress")
st.progress((st.session_state.current_question_index + 1) / len(st.session_state.questions))

# Display previous responses with better formatting
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
            st.markdown(f"**Communication Score:** {response['analysis']['communication_score']}/10")
            st.markdown("**Feedback:**")
            st.markdown(f"""<div style='padding: 1rem; background-color: #ffffff; border: 1px solid #ddd; border-radius: 0.5rem; margin-bottom: 1rem;'>
                {response['analysis']['feedback']}
            </div>""", unsafe_allow_html=True)
            st.markdown("---")