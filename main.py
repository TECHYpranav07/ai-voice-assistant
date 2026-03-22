from wake_words import listen_for_wake_word
from stt import listen
from tts import speak
from llm import ask_llm
from utils import handle_command
import time
time.sleep(5)
speak("Assistant started")
def main():
    state = "IDLE"

    print("🚀 Assistant Ready")

    while True:

        # 🟡 IDLE STATE → wait for wake word
        if state == "IDLE":
            print("🟡 Waiting for wake word...")
            if listen_for_wake_word():
                speak("Yes?")
                state = "ACTIVE"

        # 🟢 ACTIVE STATE → process commands
        elif state == "ACTIVE":
            user_input = listen()

            if not user_input:
                continue

            print("You:", user_input)

            # 🔴 Exit program
            if "exit" in user_input or "quit" in user_input:
                speak("Goodbye!")
                break

            # 😴 Go back to idle
            if "sleep" in user_input or "stop" in user_input:
                speak("Going to sleep")
                state = "IDLE"
                continue

            # ⚡ Fast command
            command_response = handle_command(user_input)

            if command_response:
                speak(command_response)
            else:
                # 🧠 AI response
                response = ask_llm("Answer shortly: " + user_input)
                speak(response)


if __name__ == "__main__":
    main()