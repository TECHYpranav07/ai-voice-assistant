import subprocess

def ask_llm(prompt):
    result = subprocess.run(
        ["ollama", "run", "tinyllama", prompt],
        capture_output=True,
        text=True,
        encoding="utf-8",   # 🔥 ADD THIS
        errors="ignore"     # 🔥 ADD THIS
    )
    return result.stdout.strip() if result.stdout else "Sorry, no response"