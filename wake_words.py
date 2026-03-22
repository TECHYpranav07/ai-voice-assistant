import speech_recognition as sr

recognizer = sr.Recognizer()

def listen_for_wake_word():
    with sr.Microphone() as source:
        recognizer.adjust_for_ambient_noise(source, duration=0.5)
        audio = recognizer.listen(source)

    try:
        text = recognizer.recognize_google(audio).lower()

        if "asus" in text:
            print("Wake word detected")
            return True
    except:
        pass

    return False