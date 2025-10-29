FROM python:3.12

WORKDIR /app

COPY requirements/requirements.prod.txt .
RUN pip install --no-cache-dir -r requirements.prod.txt

COPY . .

COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["gunicorn", "--bind", "0.0.0.0:8888", "foodgram_backend.wsgi"]
