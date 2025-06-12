from dotenv import load_dotenv
load_dotenv()
import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'hard-to-guess-string'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///users.id'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # OpenAI API key for AI analysis (optional)
    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')