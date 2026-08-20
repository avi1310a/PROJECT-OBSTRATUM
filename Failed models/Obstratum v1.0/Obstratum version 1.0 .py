import tkinter as tk
from tkinter import scrolledtext
import subprocess
import webbrowser
import threading
import os
import re
import math
import ast
import operator
from datetime import datetime

import pyttsx3
import speech_recognition as sr


# ============================================================
#                       OBSTRATUM
#              Local Windows AI Assistant
# ============================================================

ASSISTANT_NAME = "OBSTRATUM"


# ============================================================
#                 CONFIGURATION
# ============================================================

# IMPORTANT:
# Change these paths to match YOUR PC.

APPS = {
    "edge": r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",

    # VS Code
    "vscode": r"C:\Users\YOUR_USERNAME\AppData\Local\Programs\Microsoft VS Code\Code.exe",

    # Put your actual game executable paths here.
    "genshin": r"C:\PATH\TO\Genshin Impact\GenshinImpact.exe",
    "ghost of tsushima": r"C:\PATH\TO\Ghost of Tsushima\GhostOfTsushima.exe",
}


WEBSITES = {
    "youtube": "https://www.youtube.com",
    "youtube music": "https://music.youtube.com",
    "google": "https://www.google.com",
    "github": "https://github.com",
    "gmail": "https://mail.google.com",
}


# ============================================================
#                    TEXT TO SPEECH
# ============================================================

engine = pyttsx3.init()

engine.setProperty("rate", 175)
engine.setProperty("volume", 1.0)


def speak(text):
    """
    Speak text using Windows TTS.
    """

    try:
        engine.say(text)
        engine.runAndWait()
    except Exception:
        pass


# ============================================================
#                    SAFE CALCULATOR
# ============================================================

operators = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.Mod: operator.mod,
    ast.FloorDiv: operator.floordiv,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}


def safe_calculate(expression):
    """
    Safely evaluate basic mathematical expressions.

    Examples:
        25 * 48
        2 ** 10
        (50 + 20) / 2
        144 ** 0.5
    """

    expression = expression.replace("^", "**")

    try:
        tree = ast.parse(expression, mode="eval")
    except Exception:
        return None

    def evaluate(node):

        if isinstance(node, ast.Expression):
            return evaluate(node.body)

        if isinstance(node, ast.Constant):
            if isinstance(node.value, (int, float)):
                return node.value
            raise ValueError()

        if isinstance(node, ast.BinOp):
            left = evaluate(node.left)
            right = evaluate(node.right)

            operation = operators.get(type(node.op))

            if operation is None:
                raise ValueError()

            return operation(left, right)

        if isinstance(node, ast.UnaryOp):
            value = evaluate(node.operand)

            operation = operators.get(type(node.op))

            if operation is None:
                raise ValueError()

            return operation(value)

        raise ValueError()

    try:
        result = evaluate(tree)

        if isinstance(result, float):
            if result.is_integer():
                return int(result)

        return result

    except Exception:
        return None


def extract_math(command):

    command = command.lower()

    replacements = {
        "plus": "+",
        "minus": "-",
        "times": "*",
        "multiplied by": "*",
        "divided by": "/",
        "divide by": "/",
        "power": "**",
        "to the power of": "**",
        "mod": "%",
    }

    for word, symbol in replacements.items():
        command = command.replace(word, symbol)

    # Remove common phrases
    phrases = [
        "calculate",
        "what is",
        "what's",
        "solve",
        "compute",
        "answer",
        "equals",
        "equal to",
    ]

    for phrase in phrases:
        command = command.replace(phrase, "")

    # Keep mathematical characters
    expression = re.sub(
        r"[^0-9+\-*/%.() ]",
        "",
        command
    )

    expression = expression.strip()

    if not expression:
        return None

    # Avoid accidentally treating random text as math
    if not re.search(r"\d", expression):
        return None

    return expression


# ============================================================
#                     APPLICATIONS
# ============================================================

def launch_application(app_name):

    path = APPS.get(app_name)

    if not path:
        return f"I don't have a path configured for {app_name}."

    if not os.path.exists(path):
        return (
            f"I found {app_name}, but its executable path "
            f"is not configured correctly."
        )

    try:
        subprocess.Popen(path)
        return f"Launching {app_name}."

    except Exception as e:
        return f"I couldn't launch {app_name}: {e}"


# ============================================================
#                     WEBSITE SYSTEM
# ============================================================

def open_website(site):

    url = WEBSITES.get(site)

    if not url:
        return f"I don't know the website {site}."

    webbrowser.open(url)

    return f"Opening {site}."


# ============================================================
#                    QUESTION ANSWERS
# ============================================================

def answer_question(command):

    command = command.lower().strip()

    if "who are you" in command or "what are you" in command:
        return (
            "I am OBSTRATUM, your Python based desktop assistant."
        )

    if "your name" in command:
        return "My name is OBSTRATUM."

    if "hello" in command or "hi obstratum" in command:
        return "Hello. OBSTRATUM is online."

    if "how are you" in command:
        return "All systems are operational."

    if "what can you do" in command:
        return (
            "I can launch applications and websites, "
            "answer basic questions, calculate mathematics, "
            "and respond to voice commands."
        )

    if "time" in command:
        current_time = datetime.now().strftime("%I:%M %p")
        return f"The current time is {current_time}."

    if "date" in command:
        current_date = datetime.now().strftime("%d %B %Y")
        return f"Today is {current_date}."

    if "what is artificial intelligence" in command:
        return (
            "Artificial intelligence is the field of creating "
            "computer systems that can perform tasks that normally "
            "require human intelligence."
        )

    if "what is python" in command:
        return (
            "Python is a high level programming language commonly "
            "used for software, automation, artificial intelligence, "
            "data science, and robotics."
        )

    if "who made you" in command:
        return (
            "I was built as the OBSTRATUM project using Python."
        )

    return None


# ============================================================
#                    COMMAND PROCESSOR
# ============================================================

def process_command(command):

    original = command
    command = command.lower().strip()

    # Remove wake word
    command = re.sub(
        r"^(hey\s+)?obstratum[\s,:-]*",
        "",
        command
    ).strip()

    if not command:
        return "Yes?"

    # --------------------------------------------------------
    # EXIT
    # --------------------------------------------------------

    if command in [
        "exit",
        "quit",
        "close",
        "shutdown",
        "goodbye",
    ]:
        return "__EXIT__"

    # --------------------------------------------------------
    # WEBSITE COMMANDS
    # --------------------------------------------------------

    for site in WEBSITES:

        if (
            command == f"open {site}"
            or command == f"launch {site}"
            or command == site
        ):
            return open_website(site)

    # --------------------------------------------------------
    # APPLICATION COMMANDS
    # --------------------------------------------------------

    for app in APPS:

        if (
            command == f"open {app}"
            or command == f"launch {app}"
            or command == f"start {app}"
        ):
            return launch_application(app)

    # Special aliases
    aliases = {
        "microsoft edge": "edge",
        "edge browser": "edge",
        "visual studio code": "vscode",
        "code": "vscode",
        "genshin impact": "genshin",
        "ghost of tsushima director's cut": "ghost of tsushima",
    }

    for alias, app in aliases.items():

        if (
            command == f"open {alias}"
            or command == f"launch {alias}"
            or command == f"start {alias}"
        ):
            return launch_application(app)

    # --------------------------------------------------------
    # CALCULATOR
    # --------------------------------------------------------

    math_expression = extract_math(command)

    if math_expression:

        result = safe_calculate(math_expression)

        if result is not None:
            return f"The answer is {result}."

    # --------------------------------------------------------
    # BASIC QUESTIONS
    # --------------------------------------------------------

    answer = answer_question(command)

    if answer:
        return answer

    # --------------------------------------------------------
    # SEARCH GOOGLE
    # --------------------------------------------------------

    if command.startswith("search "):

        query = command[7:].strip()

        if query:
            url = (
                "https://www.google.com/search?q="
                + webbrowser.quote(query)
            )

            webbrowser.open(url)

            return f"Searching Google for {query}."

    # --------------------------------------------------------
    # YOUTUBE SEARCH
    # --------------------------------------------------------

    if command.startswith("youtube search "):

        query = command[len("youtube search "):].strip()

        if query:

            url = (
                "https://www.youtube.com/results?search_query="
                + webbrowser.quote(query)
            )

            webbrowser.open(url)

            return f"Searching YouTube for {query}."

    # --------------------------------------------------------
    # UNKNOWN COMMAND
    # --------------------------------------------------------

    return (
        "I don't know that command yet. "
        "Try saying open YouTube, open Genshin, "
        "open Edge, or calculate a mathematical expression."
    )


# ============================================================
#                    VOICE RECOGNITION
# ============================================================

recognizer = sr.Recognizer()


def listen():

    try:

        with sr.Microphone() as source:

            status_label.config(
                text="🎙️ Listening..."
            )

            recognizer.adjust_for_ambient_noise(
                source,
                duration=0.5
            )

            audio = recognizer.listen(
                source,
                timeout=5,
                phrase_time_limit=8
            )

        status_label.config(
            text="🧠 Processing..."
        )

        text = recognizer.recognize_google(
            audio
        )

        return text

    except sr.WaitTimeoutError:

        return None

    except sr.UnknownValueError:

        return None

    except sr.RequestError:

        return None

    except Exception:

        return None


def voice_command():

    def worker():

        command = listen()

        if command:

            root.after(
                0,
                lambda: handle_command(command)
            )

        else:

            root.after(
                0,
                lambda: update_status(
                    "❌ I couldn't understand that."
                )
            )

    threading.Thread(
        target=worker,
        daemon=True
    ).start()


# ============================================================
#                     GUI FUNCTIONS
# ============================================================

def update_status(text):

    status_label.config(
        text=text
    )


def add_message(sender, message):

    chat.config(
        state=tk.NORMAL
    )

    if sender == "You":

        chat.insert(
            tk.END,
            f"\nYOU  ›  {message}\n"
        )

    else:

        chat.insert(
            tk.END,
            f"OBSTRATUM  ›  {message}\n"
        )

    chat.see(
        tk.END
    )

    chat.config(
        state=tk.DISABLED
    )


def handle_command(command):

    command = command.strip()

    if not command:
        return

    add_message(
        "You",
        command
    )

    input_box.delete(
        0,
        tk.END
    )

    response = process_command(
        command
    )

    if response == "__EXIT__":

        add_message(
            "OBSTRATUM",
            "Shutting down."
        )

        speak(
            "Shutting down."
        )

        root.after(
            1000,
            root.destroy
        )

        return

    add_message(
        "OBSTRATUM",
        response
    )

    status_label.config(
        text="🟢 Ready"
    )

    threading.Thread(
        target=speak,
        args=(response,),
        daemon=True
    ).start()


def typed_command(event=None):

    command = input_box.get()

    handle_command(
        command
    )


# ============================================================
#                         GUI
# ============================================================

root = tk.Tk()

root.title(
    "OBSTRATUM"
)

root.geometry(
    "900x600"
)

root.minsize(
    700,
    450
)

root.configure(
    bg="#101114"
)


# ------------------------------------------------------------
# Header
# ------------------------------------------------------------

header = tk.Frame(
    root,
    bg="#17191f",
    height=80
)

header.pack(
    fill=tk.X
)

title = tk.Label(
    header,
    text="OBSTRATUM",
    font=("Segoe UI", 26, "bold"),
    bg="#17191f",
    fg="white"
)

title.pack(
    pady=(12, 0)
)


subtitle = tk.Label(
    header,
    text="Local Windows AI Assistant",
    font=("Segoe UI", 10),
    bg="#17191f",
    fg="#9ca3af"
)

subtitle.pack()


# ------------------------------------------------------------
# Chat
# ------------------------------------------------------------

chat = scrolledtext.ScrolledText(
    root,
    wrap=tk.WORD,
    font=("Consolas", 11),
    bg="#0d0f12",
    fg="#e5e7eb",
    insertbackground="white",
    borderwidth=0,
    padx=20,
    pady=20
)

chat.pack(
    fill=tk.BOTH,
    expand=True,
    padx=15,
    pady=15
)

chat.config(
    state=tk.DISABLED
)


# ------------------------------------------------------------
# Input Area
# ------------------------------------------------------------

bottom = tk.Frame(
    root,
    bg="#101114"
)

bottom.pack(
    fill=tk.X,
    padx=15,
    pady=(0, 15)
)


input_box = tk.Entry(
    bottom,
    font=("Segoe UI", 13),
    bg="#1b1e24",
    fg="white",
    insertbackground="white",
    relief=tk.FLAT
)

input_box.pack(
    side=tk.LEFT,
    fill=tk.X,
    expand=True,
    ipady=12,
    padx=(0, 10)
)

input_box.bind(
    "<Return>",
    typed_command
)


send_button = tk.Button(
    bottom,
    text="SEND",
    command=typed_command,
    font=("Segoe UI", 10, "bold"),
    bg="#2563eb",
    fg="white",
    activebackground="#1d4ed8",
    relief=tk.FLAT,
    padx=20,
    pady=10
)

send_button.pack(
    side=tk.LEFT,
    padx=(0, 8)
)


voice_button = tk.Button(
    bottom,
    text="🎙️ VOICE",
    command=voice_command,
    font=("Segoe UI", 10, "bold"),
    bg="#272a31",
    fg="white",
    activebackground="#343842",
    relief=tk.FLAT,
    padx=20,
    pady=10
)

voice_button.pack(
    side=tk.LEFT
)


# ------------------------------------------------------------
# Status
# ------------------------------------------------------------

status_label = tk.Label(
    root,
    text="🟢 Ready",
    font=("Segoe UI", 9),
    bg="#101114",
    fg="#9ca3af"
)

status_label.pack(
    pady=(0, 10)
)


# ------------------------------------------------------------
# Startup Message
# ------------------------------------------------------------

add_message(
    "OBSTRATUM",
    "Systems online. How can I help?"
)


# ============================================================
#                         START
# ============================================================

root.mainloop()