FROM python:3.12-alpine

WORKDIR /app
COPY main.py /app/main.py

USER 65532:65532
EXPOSE 8085

CMD ["python", "/app/main.py"]
