FROM python:3.12-slim
WORKDIR /workspace
COPY backend /workspace/backend
COPY ai /workspace/ai
COPY db /workspace/db
COPY data /workspace/data
WORKDIR /workspace/backend
RUN pip install --no-cache-dir . asyncpg python-dotenv
ENV PYTHONPATH=/workspace/backend
CMD ["sh", "-c", "alembic upgrade head && python ../db/seed/run_seed.py && python ../db/seed/load_knowledge_base.py && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
