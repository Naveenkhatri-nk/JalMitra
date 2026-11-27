# JalMitra's own AI model (Qwen3-4B Instruct through Ollama) as a Hugging Face Space (free "CPU basic").
# The model is downloaded once while the Space is built, so it starts quickly afterwards.
FROM ollama/ollama:latest

ENV OLLAMA_HOST=0.0.0.0:7860 \
    OLLAMA_MODELS=/models \
    OLLAMA_KEEP_ALIVE=24h \
    OLLAMA_NUM_PARALLEL=1 \
    OLLAMA_MAX_LOADED_MODELS=1 \
    OLLAMA_CONTEXT_LENGTH=4096 \
    HOME=/home/ollama

RUN mkdir -p /models /home/ollama \
 && (ollama serve > /tmp/build-ollama.log 2>&1 &) \
 && sleep 8 \
 && ollama pull qwen3:4b-instruct-2507-q4_K_M \
 && chmod -R a+rwX /models /home/ollama

EXPOSE 7860
# the base image already starts "ollama"; this makes it run the server
CMD ["serve"]
