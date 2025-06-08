FROM python:3.13-slim-bookworm

WORKDIR /app
COPY socks5_server.py .

EXPOSE 1080

CMD ["python", "client_auth_server.py"]