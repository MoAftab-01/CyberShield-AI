#!/bin/sh

echo "Starting Ollama..."

ollama serve &

PID=$!

MODEL=${OLLAMA_MODEL:-llama3:latest}

echo "Waiting for Ollama..."

until ollama list >/dev/null 2>&1
do
    sleep 2
done

echo "Checking model: $MODEL"

if ! ollama list | grep -q "$MODEL"; then
    echo "Downloading $MODEL..."
    ollama pull "$MODEL"
else
    echo "$MODEL already exists."
fi

wait $PID