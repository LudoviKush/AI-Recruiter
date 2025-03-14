# AI Technical Recruiter

An AI-powered technical recruiter system that conducts automated interviews for backend developer positions. The system uses speech-to-text technology and OpenAI language models to process and analyze candidate responses in real-time.

## Features

- Dynamic question generation using OpenAI GPT models
- Real-time speech-to-text conversion
- Option for both voice and text responses
- Automated technical and communication scoring
- Detailed feedback for each response
- Final assessment with pass/fail determination
- User-friendly Streamlit interface

## Prerequisites

- Python 3.8 or higher
- pip (Python package installer)
- OpenAI API key

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd ai-recruiter
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file in the root directory with your OpenAI API key:
```
OPENAI_API_KEY=your_api_key_here
GPT_MODEL=gpt-4o-mini  # or another OpenAI model of your choice
```

## Running the Application

1. Start the application:
```bash
streamlit run main.py
```

2. Open your browser and navigate to the URL shown in the Streamlit output (typically http://localhost:8501)

## Usage

1. The system will dynamically generate technical interview questions
2. For each question, you can:
   - Click "Start Recording" to record your voice response
   - Or type your response in the text area
3. Your response will be automatically transcribed (if voice) and analyzed
4. View your technical score, communication score, and detailed feedback
5. Continue through all questions to complete the interview
6. Review your final assessment with overall scores at the end

## Technical Stack

- Frontend: Streamlit
- Backend: FastAPI
- Speech-to-Text: SpeechRecognition
- Audio Processing: PyAudio, sounddevice, scipy
- Language Model: OpenAI API
- Environment Management: python-dotenv
- Data Processing: NumPy, Pandas