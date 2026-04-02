set shell := ["bash", "-lc"]

frontend_dir := "project/frontend"
frontend_port := "3000"
backend_port := "8000"

default:
  @just --list

frontend:
  cd {{frontend_dir}} && npm run dev

backend:
  BACKEND_PORT={{backend_port}} uvicorn main:app --reload --host 0.0.0.0 --port {{backend_port}}