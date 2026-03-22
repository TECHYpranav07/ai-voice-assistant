import pyttsx3

def speak(text):
    print("AI:", text)
    
    engine = pyttsx3.init()   # 🔥 re-init every time
    engine.say(text)
    engine.runAndWait()
    engine.stop()             # 🔥 important