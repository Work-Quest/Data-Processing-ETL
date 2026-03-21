FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    APP_MODE=service

WORKDIR /app

# Install dependencies
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy source code
COPY . /app

# Entry point: choose mode based on APP_MODE
CMD ["sh", "-c", "\
if [ \"$APP_MODE\" = \"service\" ]; then \
    echo 'Running ETL service...'; \
    python etl_service.py; \
elif [ \"$APP_MODE\" = \"batch\" ]; then \
    echo 'Running ETL batch pipeline...'; \
    python main.py; \
else \
    echo 'Unknown APP_MODE: $APP_MODE'; \
    exit 1; \
fi"]


