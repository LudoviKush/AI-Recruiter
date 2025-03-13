from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import speech_recognition as sr
from pydantic import BaseModel
from typing import List, Dict
import os
import json
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = FastAPI()

# Initialize OpenAI client with API key from environment
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ResponseAnalysis(BaseModel):
    technical_score: float
    communication_score: float
    feedback: str

class SpeechResponse(BaseModel):
    text: str

@app.get("/")
async def read_root():
    return {"message": "AI Recruiter API is running"}

@app.get("/questions")
async def get_questions() -> List[str]:
    try:
        completion = client.chat.completions.create(
            model=os.getenv('GPT_MODEL'),
            messages=[
                {"role": "system", "content": "You are an expert technical interviewer for backend developer positions. Generate challenging but fair questions that assess both theoretical knowledge and practical experience."}, 
                {"role": "user", "content": "Generate 5 technical interview questions for a backend developer position, focusing on System Design, API Development, Database Management, Security, and Problem Solving. Return only a JSON array of question strings without any additional formatting or explanation."}
            ]
        )
        
        # Parse the response and handle potential JSON formatting
        response_text = completion.choices[0].message.content.strip()
        try:
            # Try to parse the response directly
            questions = json.loads(response_text)
            if isinstance(questions, list) and len(questions) > 0:
                return questions
        except json.JSONDecodeError:
            # If direct parsing fails, try to extract array from text
            import re
            array_match = re.search(r'\[.*\]', response_text, re.DOTALL)
            if array_match:
                try:
                    questions = json.loads(array_match.group())
                    if isinstance(questions, list) and len(questions) > 0:
                        return questions
                except:
                    pass
        
        # Fallback to empty list in case of parsing issues
        return []
    except Exception as e:
        print(f"Error generating questions: {e}")
        # Return empty list in case of API issues
        return []

@app.post("/speech-to-text")
async def speech_to_text(audio: UploadFile = File(...)) -> Dict[str, str]:
    recognizer = sr.Recognizer()
    
    # Adjust recognizer parameters for better technical term recognition
    recognizer.energy_threshold = 300  # Increased from default
    recognizer.dynamic_energy_threshold = True
    recognizer.dynamic_energy_adjustment_damping = 0.15
    recognizer.dynamic_energy_ratio = 1.5
    
    try:
        # Save the uploaded audio file temporarily
        audio_content = await audio.read()
        with open("temp_audio.wav", "wb") as temp_file:
            temp_file.write(audio_content)
        
        # Convert speech to text with improved settings
        with sr.AudioFile("temp_audio.wav") as source:
            # Adjust microphone settings
            recognizer.adjust_for_ambient_noise(source, duration=0.5)
            audio_data = recognizer.record(source)
            text = recognizer.recognize_google(audio_data, language="en-US")
            
        return {"text": text}
    except Exception as e:
        return {"error": str(e)}

@app.post("/analyze-response")
async def analyze_response(response: SpeechResponse) -> ResponseAnalysis:
    if not response.text.strip():
        return ResponseAnalysis(
            technical_score=0.0,
            communication_score=0.0,
            feedback="Please provide a response before submitting."
        )

    try:
        completion = client.chat.completions.create(
            model=os.getenv('GPT_MODEL'),
            messages=[
                {"role": "system", "content": "You are an expert technical interviewer evaluating a backend developer candidate's response. Provide constructive feedback that highlights both strengths and areas for improvement."}, 
                {"role": "user", "content": f"Evaluate this response to a backend development question:\n{response.text}\n\nProvide evaluation in JSON format with keys: technical_score (0-10), communication_score (0-10), and feedback (string)"}
            ]
        )
        
        # Extract and clean the response text
        response_text = completion.choices[0].message.content.strip()
        
        # Try to parse the response as JSON, handling different formats
        try:
            # First attempt: direct JSON parsing
            analysis = json.loads(response_text)
        except json.JSONDecodeError:
            # Second attempt: try to extract JSON-like structure and format it
            import re
            # Look for key-value pairs in the response
            scores = re.findall(r'(["\']?(?:technical|communication)_score["\']?)\s*:\s*(\d+(?:\.\d+)?)', response_text, re.I)
            feedback = re.search(r'["\']?feedback["\']?\s*:\s*["\']([^"]+)["\']', response_text)
            
            if scores and feedback:
                analysis = {
                    'technical_score': float(next(score[1] for score in scores if 'technical' in score[0].lower())),
                    'communication_score': float(next(score[1] for score in scores if 'communication' in score[0].lower())),
                    'feedback': feedback.group(1)
                }
            else:
                # If no valid structure found, create a default response
                analysis = {
                    'technical_score': 0.0,
                    'communication_score': 0.0,
                    'feedback': 'Could not analyze response format. Please try rephrasing your answer.'
                }
        
        # Ensure scores are within valid range
        analysis['technical_score'] = max(0.0, min(10.0, float(analysis.get('technical_score', 0.0))))
        analysis['communication_score'] = max(0.0, min(10.0, float(analysis.get('communication_score', 0.0))))
        analysis['feedback'] = str(analysis.get('feedback', 'No feedback provided.'))
        
        return ResponseAnalysis(**analysis)
    except Exception as e:
        print(f"Error in analyze_response: {str(e)}")
        return ResponseAnalysis(
            technical_score=0.0,
            communication_score=0.0,
            feedback=f"An error occurred while analyzing your response. Please try again."
        )