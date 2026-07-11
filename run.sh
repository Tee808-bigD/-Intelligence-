#!/bin/bash
echo "Starting DTDL Customer Intelligence Platform..."
python scripts/init_knowledge_base.py
python -m uvicorn api.main:app --host 0.0.0.0 --port 8000 &
sleep 3
streamlit run dashboard/app.py --server.port 8501 --server.address 0.0.0.0
