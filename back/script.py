import getpass  # Importation to securely obtain passwords
import os  # Allows interaction with the operating system, such as files and environment variables
import requests  # Allows sending HTTP requests, useful for communicating with APIs

from typing import Annotated  # Allows specifying data types more precisely
from typing_extensions import TypedDict  # Allows defining structured data types, such as dictionaries

from langgraph.graph import StateGraph, START, END  # Import for creating a state graph
from langgraph.graph.message import add_messages  # Allows adding messages in the graph
from langchain_ollama import OllamaLLM  # Import Ollama's language model
from IPython.display import Image, display  # Allows displaying images in Jupyter notebooks, here for displaying a graph

from psycopg import Connection
from langgraph.prebuilt import create_react_agent
from langgraph.checkpoint.postgres import PostgresSaver

import traceback  # Allows displaying detailed information about errors if something goes wrong

# Database connection parameters
DB_URI = "postgresql://postgres:my-secret-pw@postgres-container:5432/postgres?sslmode=disable"
connection_kwargs = {
    "autocommit": True,
    "prepare_threshold": 0,
}


# Defining a state as a typed dictionary (similar to a data table)
class State(TypedDict):
    # "messages" is a list of objects, each object representing a message in the graph
    messages: Annotated[list, add_messages]

# Initializing a state graph, which allows tracking different steps in a conversation
graph_builder = StateGraph(State)

# Initializing the Ollama language model (a program that can answer questions and perform text-based tasks)
llm = OllamaLLM(model="gemma2:2b", base_url="http://ollama:11434")

# Function to process an audio file via the ASR (Automatic Speech Recognition) API
def asr(state: State):
    audio_file_path = state["messages"][-1].content  # Get the path of the audio file
    #remove the path from the state
    state["messages"].pop()
    # print(audio_file_path, "\n")  # For debugging purposes

    # URL of the ASR API
    url = "http://asr_service:9000/asr?encode=true&task=transcribe&language=en&word_timestamps=false&output=txt"

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
    response = llm.invoke([{"role": "system", "content": "You role is to be an english teacher who responds to his pupil and help him when his sentences are wrong. Your name is Mr. Smith. Answer with 5 sentences maximum. Respond using only plain text. Do not use emojis, special characters, bullet points, markdown or any formatting that is not easily readable. Your responses should be clear, direct, and professional, avoiding any unnecessary embellishments or symbols."}] + state["messages"])

    # Return the message as 'ai' (not 'human')
    return {"messages": [*state["messages"], ("ai", response)]}

def tts(state: State):
    try:
        # Text to convert into audio (last user message in the state)
        text_to_synthesize = state["messages"][-1].content

        # TTS API URL
        api_url = "http://tts_service:5002/api/tts"

        
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

        print("Audio successfully generated")

        # Return the updated state with a confirmation message
        return {
            "messages": [
                *state["messages"], 
                {
                    "role": "ai", 
                    "content": "Audio synthesis complete.", 
                    # TODO : Move the audio data to a separate key in the message to be more logical
                    "audio_data": audio_data 
                }
            ] 
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


# Function to process graph updates in response to user inputs
def stream_graph_updates(user_input: str):
    with Connection.connect(DB_URI, **connection_kwargs) as conn:
        # On crée un checkpointer avec une connexion standard
        checkpointer = PostgresSaver(conn)
        
        # IMPORTANT : appeler setup() la première fois pour créer les tables nécessaires
        checkpointer.setup()
        
        # Compilation du graph avec le checkpointer pour la persistance
        graph = graph_builder.compile(checkpointer=checkpointer)
        
        # Exemple de configuration avec un thread_id personnalisé
        config = {"configurable": {"thread_id": "3"}}

        # Example usage of the function to save the image
        #save_graph_as_png(graph, "my_graph.png")
        try:

            
            # Start the state with the user input, here a message of type "user"
            initial_state = {"messages": [{"role": "user", "content": user_input}]}
            
            # The graph processes the state and returns the events that occur
            for event in graph.stream(initial_state, config=config):
                for value in event.values():
                    # Display the last message generated by the model, which responds to the user
                    last_message = value["messages"][-1]
                    if "audio_data" in last_message:
                        print("Node: Audio produced.\n")
                    else:
                        print("Node:", last_message, "\n")

            audio_data = last_message["audio_data"]


            # Optional: Save the audio file locally (if needed)
            # with open("output.wav", "wb") as audio_file:
            #     audio_file.write(audio_data)
            # print("Generated audio successfully saved in 'output.wav'.")
                
            return audio_data
    
        except Exception as e:
            # If an error occurs, display the error message and a full traceback
            print(f"Error in stream_graph_updates: {str(e)}")
            traceback.print_exc()

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


# Main loop to interact with the user
if __name__ == "__main__":
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
