# Physics Data Platform (local backend)

This backend is a **local-first** API that supports:

- Multi-user accounts (register/login)
- Notebook storage (upload/download `.ipynb` content)
- Sharing (public notebooks + share-with-specific-users)

It’s designed so a future UI can provide **multiple panes** (graphs, data tables, paper breakdowns) while using this service for persistence and collaboration.

## Quickstart (local)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt

export PDP_SECRET_KEY="dev-secret-change-me"
export PDP_DB_URL="sqlite:///./data/app.sqlite3"
export PDP_NOTEBOOK_STORAGE_DIR="./data/notebooks"

uvicorn backend.app.main:app --reload --port 8000
```

Then visit `http://localhost:8000/docs`.

## Core concepts

- **Notebook**: metadata in SQLite + content stored as a file on disk
- **Ownership**: each notebook has an owner
- **Sharing**:
  - `is_public=true` allows anyone to read
  - otherwise the owner can share with specific users

## Useful endpoints (high level)

- `POST /auth/register`
- `POST /auth/token` (password grant; returns JWT)
- `GET /users/me`
- `POST /notebooks` (create notebook metadata)
- `PUT /notebooks/{id}/content` (upload `.ipynb`)
- `GET /notebooks/{id}` (metadata)
- `GET /notebooks/{id}/content` (download)
- `POST /notebooks/{id}/share` (share with another user)

