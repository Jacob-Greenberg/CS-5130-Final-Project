import os
import json
import re
from adb_interface import TouchInterface
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

PROMPT_FILE_NAME = "prompt.txt"
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Gemini setup
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

# Load the system prompt from the local file
with open(PROMPT_FILE_NAME, "r") as file:
    system_prompt = file.read()

# Get the user prompt
user_prompt = input("Enter the condition you would like to be tested: ")
prompt = system_prompt + user_prompt + "\n###END TESTER PROMPT###"

ti = TouchInterface()
chat = model.start_chat(history=[])

def enter_input():
    # Get current screen XML
    ti.dump_ui_hierarchy()

    # Make it useful to us
    with open('window_dump.xml', "r") as file:
        hierarchy = file.read()
    
    # Send the hierarchy and prompt to Gemini
    response = chat.send_message(f"{hierarchy}\n\n{prompt}")
    
    print("==========")
    print(response.text)
    print("==========")
    
    try:
        cleaned_json = re.sub(r'```\s*\w*\s*|\s*```', '', response.text.strip())
        response_json = json.loads(cleaned_json)
        return response_json
    except json.JSONDecodeError:
        print("Error: Unable to parse JSON response")
        return None

def perform_action(action):
    if not action:
        return

    try:
        if 'touch' in action['command']:
            x, y = action['command'].split()[1:3]
            ti.touch(x, y)
        elif 'swipe' in action['command']:
            x_start, y_start, x_end, y_end, duration = action['command'].split()[1:6]
            ti.swipe(x_start, y_start, x_end, y_end, duration)
        elif 'text' in action['command']:
            text = action['command'].split(None, 1)[1]
            ti.text(text)
        elif 'key' in action['command']:
            keycode = action['command'].split()[1]
            ti.key(keycode)
        else:
            print("Invalid command received")
    except (IndexError, KeyError):
        print("Error: Invalid action format")

print("Querying Gemini")
response_json = enter_input()
perform_action(response_json)

while response_json and response_json.get('command') not in ["end", "error"]:
    response_json = enter_input()
    perform_action(response_json)
