import getpass  # Importation to securely obtain passwords
import os  # Allows interaction with the operating system, such as files and environment variables
import requests  # Allows sending HTTP requests, useful for communicating with APIs

from typing import Annotated  # Allows specifying data types more precisely
from typing_extensions import TypedDict  # Allows defining structured data types, such as dictionaries

from langgraph.graph import StateGraph, START, END  # Import for creating a state graph
from langgraph.graph.message import add_messages  # Allows adding messages in the graph
from langchain_ollama import OllamaLLM  # Import Ollama's language model
from IPython.display import Image, display  # Allows displaying images in Jupyter notebooks, here for displaying a graph

import traceback  # Allows displaying detailed information about errors if something goes wrong


# Function to set an environment variable if it is not already defined
def _set_env(var: str):
    if not os.environ.get(var):  # Checks if the variable doesn't already exist in the environment
        os.environ[var] = getpass.getpass(f"{var}: ")  # If the variable doesn't exist, asks the user to enter it securely

# Defining a state as a typed dictionary (similar to a data table)
class State(TypedDict):
    # "messages" is a list of objects, each object representing a message in the graph
    messages: Annotated[list, add_messages]

# Initializing a state graph, which allows tracking different steps in a conversation
graph_builder = StateGraph(State)

# Initializing the Ollama language model (a program that can answer questions and perform text-based tasks)
llm = OllamaLLM(model="gemma2:2b")

# Function to process an audio file via the ASR (Automatic Speech Recognition) API
def asr(state: State):
    audio_file_path = state["messages"][-1].content  # Get the path of the audio file
    #remove the path from the state
    state["messages"].pop()
    # print(audio_file_path, "\n")  # For debugging purposes

    # URL of the ASR API
    url = "http://0.0.0.0:9000/asr?encode=true&task=transcribe&language=en&word_timestamps=false&output=txt"

    try:
        # Determine the file extension
        _, ext = os.path.splitext(audio_file_path)
        # Set the appropriate MIME type based on the file extension
        if ext.lower() == ".wav":
            mime_type = "audio/wav"
        elif ext.lower() == ".mp3":
            mime_type = "audio/mpeg"
        else:
            raise ValueError("Unsupported audio format")

        # Open the audio file and send it to the API
        with open(audio_file_path, "rb") as audio_file:
            files = {"audio_file": (audio_file_path, audio_file, mime_type)}
            headers = {"accept": "application/json"}
            response = requests.post(url, files=files, headers=headers)  # Send the request to the API
            response.raise_for_status()  # Raise an exception if the request fails
            transcription = response.text.strip()  # Get the transcription (text)

            # TODO: Add validation of the transcription quality here

            # Return the state with the transcription message
            return {"messages": [*state["messages"], ("user", transcription)]}

    except Exception as e:
        # In case of an error, add an error message to the graph
        return {"messages": [*state["messages"], ("system", str(e))]}

    
# Chatbot function: invokes the language model to respond to the user with text
def chatbot(state: State):
    # Generate the response with the model
    # print(state["messages"])
    response = llm.invoke([{"role": "system", "content": "You role is to be an english teacher who responds to his pupil and help him when his sentences are wrong. Your name is Mr. Smith."}] + state["messages"])

    
    # Return the message as 'ai' (not 'human')
    return {"messages": [*state["messages"], ("ai", response)]}

def tts(state: State):
    try:
        # Text to convert into audio (last user message in the state)
        text_to_synthesize = state["messages"][-1].content

        # TTS API URL
        api_url = "http://[::1]:5002/api/tts"
        
        # Parameters for the GET request
        params = {
            "text": text_to_synthesize,  # Text to synthesize
            "speaker_id": "p299",       # Speaker ID (modifiable)
            "style_wav": "",            # Optional parameter for style
            "language_id": ""           # Optional parameter for language
        }

        # Sending the GET request to the API
        response = requests.get(api_url, params=params)

        # Checking the response status
        response.raise_for_status()

        # Retrieving the audio content (wav file)
        audio_data = response.content

        # Optional: Save the audio file locally (if needed)
        with open("output.wav", "wb") as audio_file:
            audio_file.write(audio_data)

        print("Audio successfully generated and saved in 'output.wav'.")

        # Return the updated state with a confirmation message
        return {
            "messages": [*state["messages"], {"role": "system", "content": "Audio synthesis complete."}]
        }

    except Exception as e:
        # In case of an error, return the state with an error message
        return {
            "messages": [*state["messages"], {"role": "system", "content": f"Error in TTS: {str(e)}"}]
        }

# Add an edge (a "connection") from the starting point (START) to the ASR node (for audio processing)
graph_builder.add_edge(START, "asr")
# Add the ASR node to the graph
graph_builder.add_node("asr", asr)

# Add a relation between the ASR node and the chatbot node, to continue after transcription
graph_builder.add_edge("asr", "chatbot")
# Add the chatbot node to the graph
graph_builder.add_node("chatbot", chatbot)

# Add a relation between the chatbot and the TTS node, to generate audio from the chatbot's response
graph_builder.add_edge("chatbot", "tts")
graph_builder.add_node("tts", tts)

# Add a relation to finish the graph after the chatbot
graph_builder.add_edge("tts", END)

# Compile the graph, which allows executing the defined steps in order
graph = graph_builder.compile()

# Function to save the graph as a PNG image
def save_graph_as_png(graph, filename="graph.png"):
    try:
        # Generate the PNG image of the graph
        png_image = graph.get_graph().draw_mermaid_png()
        
        # Save the image to the current file
        with open(filename, "wb") as file:
            file.write(png_image)
        
        print(f"Graph image saved as {filename}")
    
    except Exception as e:
        print(f"An error occurred while saving the graph image: {str(e)}")

# Example usage of the function to save the image
save_graph_as_png(graph, "my_graph.png")


# Function to process graph updates in response to user inputs
def stream_graph_updates(user_input: str):
    try:
        # Start the state with the user input, here a message of type "user"
        initial_state = {"messages": [{"role": "user", "content": user_input}]}
        
        # The graph processes the state and returns the events that occur
        for event in graph.stream(initial_state):
            for value in event.values():
                # Display the last message generated by the model, which responds to the user
                print("Node:", value["messages"][-1], "\n")
    
    except Exception as e:
        # If an error occurs, display the error message and a full traceback
        print(f"Error in stream_graph_updates: {str(e)}")
        traceback.print_exc()


# Main loop to interact with the user
while True:
    try:
        # Ask for user input (audio file or text)
        user_input = input("User (enter audio file path or text): ")
        
        # If the user enters "quit", "exit", or "q", exit the loop and say goodbye
        if user_input.lower() in ["quit", "exit", "q"]:
            print("Goodbye!")
            break

        # Send the user input for processing by the graph
        stream_graph_updates(user_input)
    
    except:
        # If an error occurs during input reading or processing, display an error message
        user_input = "Error occurred in user input processing."
        print("User: " + user_input)
        stream_graph_updates(user_input)  # Process the error with the graph
        break  # Exit the loop after the error
