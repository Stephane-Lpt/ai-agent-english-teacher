# ai-agent-english-teacher
Project to make accessible the use of an ai english teacher. All models are running locally on docker containers : asr, llm, tts. The models are the smallest possible (1b, 3b) to be usable even on cpus.

I would like to allow users to create their own context (where encounter takes place, when, with whom) and also their own instructions like correct grammar, give C1 vocabular suggestions)

Planning
- [x] Web interface : pushMessage(sender, message) to display messages + record button
- [x] Searching for docker containers online for each model needed (asr, llm, tts)
- [] Use Langchain and Langgraph to make the pipeline
    - [] LLM
    - [] ASR
    - [] TTS
- [] Make possible to read the user messages aloud

Possible additional functionalities to consider
- [] RAG