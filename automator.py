import os
import json
from ollama import chat, ChatResponse, Client
from adb_interface import TouchInterface

PROMPT_FILE_NAME = "prompt.txt"
LLM_MODEL = 'llama3.2:3b' #'llama2-uncensored'
OLLAMA_HOST_IP = '127.0.0.1:11434'

# Load the system prompt from the local file
system_prompt = ""

with open(PROMPT_FILE_NAME) as file:
    system_prompt = system_prompt.join(file)

# Get the user prompt
user_prompt = input("Enter the condition you would like to be tested: ")
prompt = system_prompt + user_prompt + "\n###END TESTER PROMPT###"

llm_client = Client(
    host=OLLAMA_HOST_IP,
    timeout = 300
)

ti = TouchInterface()

def enter_input():

    # Get current screen XML
    ti.dump_ui_hierarchy()

    # Make it useful to us
    hierarchy = ""
    with open('window_dump.xml') as file:
        hierarchy = hierarchy.join(file)
    
    # Plug everything into a chat
    response: ChatResponse = llm_client.chat(model=LLM_MODEL, messages=[{'role':'user','content': hierarchy}, {'role':'system', 'content':prompt}])
    print("==========")
    print(response)
    print("==========")
    response_json = json.loads(response['message']['content'])
    return response_json

def preform_action(action: json):
    try:
        if 'touch' in action['command']: # touch <X Pixel> <Y Pixel>
            x = action['command'].split(" ")[1]
            y = action['command'].split(" ")[2]
            ti.touch(x, y)

        elif 'swipe' in action['command']: # swipe <X Starting Pixel> <Y Starting Pixel> <X Ending Pixel> <Y Endind Pixel> <Duration (ms)>
            x_start  = action['command'].split(" ")[1]
            y_start  = action['command'].split(" ")[2]
            x_end    = action['command'].split(" ")[3]
            y_end    = action['command'].split(" ")[4]
            duration = action['command'].split(" ")[5]
            ti.swipe(x_start, y_start, x_end, y_end, duration)

        elif 'text' in action['command']: # text <text to enter>
            text = action['command'].split(" ")[1]
            ti.text(text)

        elif 'key' in action['command']: # key <android/adb keycode>
            keycode = action['command'].split(" ")[1]
            ti.key(keycode)

        else:
            # AI gave us an invalid response :(
            pass
    except IndexError as e:
        pass
        # AI gave us an invalid response

print("Querying LLM")
response_json = enter_input()
preform_action(response_json)

while(response_json['command'] != "end" or response_json['command'] != "error"):
    
    response_json = enter_input()
    preform_action(response_json)
