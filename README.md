# Ai agent: english teacher
## Project to make accessible the use of an ai english teacher. 
- All models are running locally on docker containers : asr, llm, tts. 
- The models are the smallest possible (1b, 3b) to be usable even on cpus.

I would like to allow users to create their own context (where encounter takes place, when, with whom) and also their own instructions like correct grammar, give C1 vocabular suggestions)
## Prerequisites
- Install docker engine
  - Windows: [Docker Desktop](https://desktop.docker.com/win/main/amd64/Docker%20Desktop%20Installer.exe?utm_source=docker&utm_medium=webreferral&utm_campaign=docs-driven-download-win-amd64) or [WSL](https://learn.microsoft.com/en-us/windows/wsl/install)
  - Ubuntu: [Installation Guide](https://docs.docker.com/engine/install/ubuntu/#install-using-the-repository)
  - Other Linux distributions: [Installation Guide](https://docs.docker.com/engine/install/)
## Installation
- ```docker compose up -d``` or (if you have a gpu)```docker compose -f docker-compose-gpu.yml up -d```
- Wait 5 minutes to pull all the images (just for the first time)
- Wait 1 minute after starting the docker stack because some services like ollama needs to pull the model (just for the first time, then it is like 10 seconds)
- Go at page to start the conversation: [http://localhost:8080](http://localhost:8080)
## Planning
BACK: 
- [x] Web interface : pushMessage(sender, message) to display messages + record button
- [x] Searching for docker containers online for each model needed (asr, llm, tts)
- [x] Use Langgraph to make the pipeline
    - [x] LLM
    - [x] ASR
    - [x] TTS
- [x] Save the current state of conversation in database
- [] Benchmark the different models for asr, llm, tts
- [] Give a good prompt to the tutor
FRONT:
- [x] Make possible to read the user messages aloud

GENERAL:
- [] Change the language of the tutor easily
- [] Let the user choose his own context of conversation
- [] Let the user choose the length of the english tutor responses
- [] Let the user choose if he wants a real fluent conversation with an endpoint detection or being capacle to redo their audio

## Possible additional functionalities to consider
- [] Rate the pronunciation performance of the speaker and help him by giving him the phonemes of the right pronunciation if any errors.
- [] Have a lightweight avatar
- [] RAG to rate the best responses


## Justification
- Why using Langgraph instead of Langchain :
    - My application requires decisions or branching workflows, like:
        - If ASR confidence < 70%, ask the user to repeat.
        - If grammar is correct but pronunciation is poor, suggest phonetic practice.

