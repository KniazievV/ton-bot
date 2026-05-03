FROM python:3.11-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# База SQLite в ./data — при деплое смонтируйте том на /app/data, иначе при пересоздании контейнера список кошельков обнулится.
CMD ["python", "main.py"]
