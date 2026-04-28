import base64
import os
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

#print(os.environ.get("GEMINI_API_KEY"))

client = genai.Client(
        api_key = os.environ.get("GEMINI_API_KEY"),
    )

model = "gemini-flash-lite-latest"

tools = [
    types.Tool(googleSearch = types.GoogleSearch(
    )),
]

generate_content_config = types.GenerateContentConfig(
    temperature = 0,
    thinking_config = types.ThinkingConfig(
        thinking_budget=0,
    ),
    tools = tools,
    system_instruction = [
        types.Part.from_text(text = """your task is to provide stock trading decision. You provide advise whether the stock mentioned should be bought or sell. You may also provide the top stocks to watch out for. """),
    ],
)

def generate():
    client = genai.Client(
        api_key = os.environ.get("GEMINI_API_KEY"),
    )

    model = "gemini-flash-lite-latest"

    tools = [
        types.Tool(googleSearch = types.GoogleSearch(
        )),
    ]

    generate_content_config = types.GenerateContentConfig(
        temperature = 0,
        thinking_config = types.ThinkingConfig(
            thinking_budget = 0,
        ),
        tools = tools,
        system_instruction = [
            types.Part.from_text(text="""your task is to provide stock trading decision. You provide advise whether the stock mentioned should be bought or sell. You may also provide the top stocks to watch out for. """),
        ],
    )

    conversation = []

    print("Chat: How can i help you? (type '/exit' to Quit and '/clear' to clear chat history): ")
    
    while True:

        user_Input = input("You: ")

        if user_Input.lower() == "/exit":
            break
        elif user_Input.lower() == "/clear":
            conversation = []
            print("Chat history cleared.\n")
            print("Chat: How can i help you? (type '/exit' to Quit and '/clear' to clear chat history): ")
            continue

        conversation.append(
            types.Content(
                role="user",
                parts=[types.Part.from_text(text=user_Input)],
            )
        )
        
        print("Chat: ", end="")

        chat_text = "" 
        for chunk in client.models.generate_content_stream(
            model=model,
            contents=conversation,
            config=generate_content_config,
        ):
            if chunk.text:
                print(chunk.text, end="", flush = True)
                chat_text += chunk.text

        print("\n") 

        conversation.append(
            types.Content(
                role="model",
                parts=[types.Part.from_text(text=chat_text)],
            )   
        )

def generate_once(conversation):


    chat_text = "" 
    for chunk in client.models.generate_content_stream(
        model = model,
        contents = conversation,
        config = generate_content_config,
    ):
        if chunk.text:
            chat_text += chunk.text

    return chat_text

    
