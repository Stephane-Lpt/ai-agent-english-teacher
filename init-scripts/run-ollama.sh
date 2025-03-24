#!/bin/bash

apt update
apt install curl -y

echo "Starting Ollama server..."
ollama serve &


echo "Waiting for Ollama server to be active..."
while [ -z "$(ollama list | grep 'NAME')" ]; do
  sleep 1
done

echo "OK: It's active..."

echo "Trying to install the model..."2
ollama run gemma2:2b

echo "The model is installed..."

# This will keep the script running
tail -f /dev/null
