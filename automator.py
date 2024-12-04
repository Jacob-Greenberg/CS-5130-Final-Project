import os
import json
from uiautomator import Device
from ollama import chat, ChatResponse, Client

PROMPT_FILE_NAME = "prompt.txt"
DEVICE_SERIAL = '5110016020032640'
LLM_MODEL = 'llama2-uncensored'
OLLAMA_HOST_IP = '127.0.0.1:11434'



# Load the system prompt from the local file
system_prompt = ""

with open(PROMPT_FILE_NAME) as file:
    system_prompt = system_prompt.join(file)

# Get the user prompt
user_prompt = input("Enter the condition you would like to be tested: ")
prompt = system_prompt + user_prompt + "\n###END TESTER PROMPT###"

llm_client = Client(
    host=OLLAMA_HOST_IP
)

def enter_input():

    # Get current screen XML
    phone.dump("hierarchy.xml")

    # Make it useful to us
    hierarchy = ""
    with open('hierarchy.xml') as file:
        hierarchy = hierarchy.join(file)
    
    # Plug everything into a chat
    response: ChatResponse = llm_client.chat(model=LLM_MODEL, messages=[{'role':'user','content':prompt + hierarchy}])
    response_json = json.loads(response['message']['content'])
    print(response_json)
    return response_json

phone = Device(DEVICE_SERIAL) # Get a reference to the device

response_json = enter_input()

while(response_json['command'] != "end" or response_json['command'] != "error"):
    
    response_json = enter_input
    print(response_json)
    phone.press(response_json['command'])





#phone.press()

#COMMAND_MAP = {
#"home": phone.press.home(),
#"back": phone.press.back(),
#"left": phone.press.left(),
#"right": phone.press.right(),
#"up": phone.press.up(),
#"down": phone.press.down(),
#"center": phone..press,
#"menu": phone.,
#"search": phone.,
#"enter": phone.,
#"delete": phone.,
#"recent": phone.,
#"camera": phone.,
#"power": phone.,
#}