FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY src ./src
COPY data ./data
ENV PYTHONPATH=/app/src
EXPOSE 8000
# Set JOBSEARCH_API_KEY at run time: docker run -e JOBSEARCH_API_KEY=... -p 8000:8000 jobsearch
CMD ["uvicorn", "jobsearch.api:app", "--host", "0.0.0.0", "--port", "8000"]
