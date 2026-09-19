FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .
COPY jev_lab ./jev_lab
COPY data ./data
COPY assets ./assets
COPY static ./static

ENV HOST=0.0.0.0
ENV PORT=7872

EXPOSE 7872
CMD ["python", "app.py"]
