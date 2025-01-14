import getpass
import os
import requests

from typing import Annotated
from typing_extensions import TypedDict

from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_ollama import OllamaLLM
from IPython.display import Image, display


import traceback


# Fonction pour définir une variable d'environnement si elle n'est pas déjà définie
def _set_env(var: str):
    if not os.environ.get(var):  # Vérifie si la variable n'existe pas déjà
        os.environ[var] = getpass.getpass(f"{var}: ")  # Demande une entrée sécurisée à l'utilisateur

# Définition d'un état comme un dictionnaire typé
class State(TypedDict):
    # La clé "messages" est un type liste, annoté pour permettre des opérations spécifiques (comme `add_messages`)
    messages: Annotated[list, add_messages]

# Initialisation d'un graphe d'état avec le type défini
graph_builder = StateGraph(State)

# Initialisation du modèle de langage Ollama
llm = OllamaLLM(model="llama3.2:1b")

# Fonction pour traiter un fichier audio via l'API ASR
def asr(state: State):
    audio_file_path = state["messages"][-1].content  # Récupère le chemin du fichier audio
    print(audio_file_path)
    url = "http://0.0.0.0:9000/asr?encode=true&task=transcribe&language=en&word_timestamps=false&output=txt"
    try:
        with open(audio_file_path, "rb") as audio_file:
            files = {"audio_file": (audio_file_path, audio_file, "audio/mpeg")}
            headers = {"accept": "application/json"}
            response = requests.post(url, files=files, headers=headers)
            response.raise_for_status()  # Lève une exception si la requête échoue
            transcription = response.text.strip()  # Récupère la transcription
            return {"messages": [*state["messages"], ("assistant", transcription)]}
    except Exception as e:
        return {"messages": [*state["messages"], ("system", str(e))]}
    
# Fonction chatbot : invoque le modèle de langage avec le texte
def chatbot(state: State):
    return {"messages": [llm.invoke(state["messages"])]}

# Ajout du nœud ASR au graphe
graph_builder.add_edge(START, "asr")
graph_builder.add_node("asr", asr)

# Ajout du nœud chatbot après ASR
graph_builder.add_edge("asr", "chatbot")
graph_builder.add_node("chatbot", chatbot)

# Ajout de la fin du graphe
graph_builder.add_edge("chatbot", END)

# Compilation du graphe
graph = graph_builder.compile()

# Essayez d'afficher une représentation graphique du graphe
try:
    display(Image(graph.get_graph().draw_mermaid_png()))  # Dessine le graphe en utilisant Mermaid
except Exception:
    pass

# Fonction pour traiter les mises à jour du graphe en réponse aux entrées utilisateur
def stream_graph_updates(user_input: str):
    try:
        # Ajout direct de l'entrée utilisateur comme message valide
        initial_state = {"messages": [{"role": "user", "content": user_input}]}
        for event in graph.stream(initial_state):
            for value in event.values():
                # Affiche la dernière réponse générée par le modèle
                print("Assistant:", value["messages"][-1])
    except Exception as e:
        # Affiche une trace complète de l'exception
        print(f"Error in stream_graph_updates: {str(e)}")
        traceback.print_exc()


# Boucle principale pour interagir avec l'utilisateur
while True:
    try:
        # Demande une entrée utilisateur ou un fichier audio
        user_input = input("User (enter audio file path or text): ")
        if user_input.lower() in ["quit", "exit", "q"]:  # Vérifie si l'utilisateur veut quitter
            print("Goodbye!")
            break

        # Envoie l'entrée utilisateur pour traitement
        stream_graph_updates(user_input)
    except:
        user_input = "Error occurred in user input processing."
        print("User: " + user_input)
        stream_graph_updates(user_input)
        break
