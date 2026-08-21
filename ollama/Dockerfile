FROM ollama/ollama:latest

COPY entrypoint.sh /entrypoint.sh

# Normalize Windows CRLF line endings to Linux LF
# and make the script executable.
RUN sed -i 's/\r$//' /entrypoint.sh \
    && chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]