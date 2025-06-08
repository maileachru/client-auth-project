FROM python:3.10-slim

WORKDIR /app
COPY socks5_server.py .

EXPOSE 1080

CMD ["python", "client_auth_server.py"]