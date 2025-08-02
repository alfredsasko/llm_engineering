#!/bin/sh
ollama serve  &
sleep 5  # Ensure the server is ready before pulling models
ollama pull llama3.2:latest
ollama pull deepseek-r1:1.5b
wait %1