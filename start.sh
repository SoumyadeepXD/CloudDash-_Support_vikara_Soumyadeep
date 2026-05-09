#!/bin/bash
export PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=python
source venv/bin/activate
uvicorn main:app --reload
