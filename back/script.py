import getpass  # Importation pour obtenir des mots de passe de manière sécurisée
import os  # Permet d'interagir avec le système d'exploitation, comme les fichiers et les variables d'environnement
import requests  # Permet d'envoyer des requêtes HTTP, utile pour communiquer avec des API

from typing import Annotated  # Permet de spécifier des types de données plus précisément
from typing_extensions import TypedDict  # Permet de définir des types de données structurés, comme des dictionnaires

from langgraph.graph import StateGraph, START, END  # Importation pour créer un graphe d'états
from langgraph.graph.message import add_messages  # Permet d'ajouter des messages dans le graphe
from langchain_ollama import OllamaLLM  # Importation du modèle de langage d'Ollama
from IPython.display import Image, display  # Permet d'afficher des images dans Jupyter notebooks, ici pour afficher un graphe

import traceback  # Permet d'afficher des informations détaillées sur les erreurs si quelque chose ne fonctionne pas


# Fonction pour définir une variable d'environnement si elle n'est pas déjà définie
def _set_env(var: str):
    if not os.environ.get(var):  # Vérifie si la variable n'existe pas déjà dans l'environnement
        os.environ[var] = getpass.getpass(f"{var}: ")  # Si la variable n'existe pas, demande à l'utilisateur de la saisir de manière sécurisée

# Définition d'un état comme un dictionnaire typé (un peu comme un tableau d'informations)
class State(TypedDict):
    # "messages" est une liste d'objets, chaque objet représentant un message dans le graphe
    messages: Annotated[list, add_messages]

# Initialisation d'un graphe d'état, ce qui permet de suivre les différentes étapes dans une conversation
graph_builder = StateGraph(State)

# Initialisation du modèle de langage Ollama (un programme qui peut répondre aux questions et effectuer des tâches avec du texte)
llm = OllamaLLM(model="llama3.2:1b")

# Fonction pour traiter un fichier audio via l'API ASR (Reconnaissance automatique de la parole)
def asr(state: State):
    audio_file_path = state["messages"][-1].content  # On récupère le chemin du fichier audio envoyé par l'utilisateur
    # print(audio_file_path, "\n")  # On affiche ce chemin (utile pour vérifier si c'est le bon fichier)
    
    # URL de l'API ASR qui va convertir l'audio en texte
    url = "http://0.0.0.0:9000/asr?encode=true&task=transcribe&language=en&word_timestamps=false&output=txt"
    
    try:
        # Ouvre le fichier audio et l'envoie à l'API pour obtenir une transcription (du texte)
        with open(audio_file_path, "rb") as audio_file:
            files = {"audio_file": (audio_file_path, audio_file, "audio/mpeg")}
            headers = {"accept": "application/json"}
            response = requests.post(url, files=files, headers=headers)  # Envoie la requête à l'API
            response.raise_for_status()  # Si la requête échoue, une exception est levée
            transcription = response.text.strip()  # Récupère la transcription (le texte)
            
            # TODO: Ajouter une vérification de la qualité de la transcription ici

            # On retourne l'état avec le message de la transcription, pour l'ajouter au graphe
            return {"messages": [*state["messages"], ("user", transcription)]}
    
    except Exception as e:
        # Si une erreur se produit, on ajoute un message d'erreur dans le graphe
        return {"messages": [*state["messages"], ("system", str(e))]}
    
# Fonction chatbot : invoque le modèle de langage pour répondre à l'utilisateur avec du texte
def chatbot(state: State):
    # On génère la réponse avec le modèle
    response = llm.invoke(state["messages"])
    
    # On retourne le message en tant que 'ai' (et non 'human')
    return {"messages": [*state["messages"], ("ai", response)]}

# Ajout d'une relation (un "edge") du point de départ (START) au nœud ASR (pour le traitement audio)
graph_builder.add_edge(START, "asr")
# Ajout du nœud ASR au graphe
graph_builder.add_node("asr", asr)

# Ajout d'une relation entre le nœud ASR et le nœud chatbot, pour continuer après la transcription
graph_builder.add_edge("asr", "chatbot")
# Ajout du nœud chatbot au graphe
graph_builder.add_node("chatbot", chatbot)

# Ajout d'une relation pour terminer le graphe après le chatbot
graph_builder.add_edge("chatbot", END)

# Compilation du graphe, ce qui permet d'exécuter les étapes définies dans l'ordre
graph = graph_builder.compile()

# Fonction pour sauvegarder le graphe en tant qu'image PNG
def save_graph_as_png(graph, filename="graph.png"):
    try:
        # Générer l'image PNG du graphe
        png_image = graph.get_graph().draw_mermaid_png()
        
        # Sauvegarder l'image dans le fichier courant
        with open(filename, "wb") as file:
            file.write(png_image)
        
        print(f"Graph image saved as {filename}")
    
    except Exception as e:
        print(f"An error occurred while saving the graph image: {str(e)}")

# Exemple d'utilisation de la fonction pour sauvegarder l'image
save_graph_as_png(graph, "my_graph.png")


# Fonction pour traiter les mises à jour du graphe en réponse aux entrées utilisateur
def stream_graph_updates(user_input: str):
    try:
        # On commence l'état avec l'entrée utilisateur, ici un message de type "user"
        initial_state = {"messages": [{"role": "user", "content": user_input}]}
        
        # Le graphe traite l'état et renvoie les événements qui se produisent
        for event in graph.stream(initial_state):
            for value in event.values():
                # Affiche le dernier message généré par le modèle, qui répond à l'utilisateur
                print("Node:", value["messages"][-1], "\n")
    
    except Exception as e:
        # Si une erreur se produit, on affiche le message d'erreur et une trace complète
        print(f"Error in stream_graph_updates: {str(e)}")
        traceback.print_exc()


# Boucle principale pour interagir avec l'utilisateur
while True:
    try:
        # Demande une entrée utilisateur (fichier audio ou texte)
        user_input = input("User (enter audio file path or text): ")
        
        # Si l'utilisateur entre "quit", "exit" ou "q", on arrête la boucle et on dit au revoir
        if user_input.lower() in ["quit", "exit", "q"]:
            print("Goodbye!")
            break

        # Envoie l'entrée de l'utilisateur pour traitement par le graphe
        stream_graph_updates(user_input)
    
    except:
        # Si une erreur se produit pendant la lecture ou le traitement, on affiche un message d'erreur
        user_input = "Error occurred in user input processing."
        print("User: " + user_input)
        stream_graph_updates(user_input)  # Traite l'erreur avec le graphe
        break  # Quitte la boucle après l'erreur
