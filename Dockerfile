FROM python:3.13-slim-bookworm

WORKDIR /app
COPY client_auth_server.py .

EXPOSE 1080

CMD ["python", "client_auth_server.py"]