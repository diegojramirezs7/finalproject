# Import the required module for text to speech conversion 
from gtts import gTTS
import time
import os

def tts(s, filename):
    language = 'en-GB'
      
    # Passing the text and language to the engine,  
    # here we have marked slow=False. Which tells  
    # the module that the converted audio should  
    # have a high speed 
    myobj = gTTS(text=s, lang=language, slow=False) 
      
    # Saving the converted audio in a mp3 file named 
    # welcome
    fs = filename+".mp3"
    path = "ttsfiles/"+fs
    myobj.save(path) 
