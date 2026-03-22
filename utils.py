import webbrowser
import os
import datetime

def handle_command(text):
    text = text.lower()

    # 🌐 Web
    if "open youtube" in text:
        webbrowser.open("https://youtube.com")
        return "Opening YouTube"

    if "open google" in text:
        webbrowser.open("https://google.com")
        return "Opening Google"

    # 💻 Apps
    if "open chrome" in text:
        os.system("start chrome")
        return "Opening Chrome"

    if "open vscode" in text:
        os.system("code")
        return "Opening VS Code"

    # ⏰ Time
    if "time" in text:
        now = datetime.datetime.now().strftime("%H:%M")
        return f"The time is {now}"

    # 🔴 System Control (BE CAREFUL)
    if "shutdown" in text:
        return "Say confirm shutdown to proceed"

    if "restart" in text:
        os.system("shutdown /r /t 5")
        return "Restarting in 5 seconds"

    return None