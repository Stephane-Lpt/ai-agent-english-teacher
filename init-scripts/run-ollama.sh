#!/bin/bash

echo "Starting Ollama server..."
ollama serve &


echo "Waiting for Ollama server to be active..."
while [ -z "$(ollama list | grep 'NAME')" ]; do
  sleep 1
done

echo "OK: It's active..."

echo "Trying to install the model..."
ollama run gemma2:2b

# Check if the model is available
if ! ollama list | grep -q "gemma2:2b"; then
  sleep 5  # Wait for download to complete
fi

# This will keep the script running
tail -f /dev/null
