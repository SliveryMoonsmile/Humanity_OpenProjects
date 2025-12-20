# Physics Data Platform — product + technical outline

## What the UI should feel like (multi-pane)

- A **workspace** made of resizable panes (split vertically/horizontally)
- Each pane hosts a **widget**:
  - **Graph pane**: plot time series / spectra / histograms (Plotly is a good default)
  - **Data pane**: tabular data viewer (filter/sort, CSV import)
  - **Paper pane**: PDF/Markdown viewer + “breakdown” sections (abstract, assumptions, derivations, results)
  - **Notebook pane**: renders `.ipynb` output cells + lets you open/download/edit in Jupyter locally

## Why notebooks matter for collaboration

Notebooks become the “unit of sharing”:
- store the raw `.ipynb`
- associate metadata (title/description/tags later)
- allow sharing (public or explicit users)

The current backend implements that base so you can iterate on the UI without losing work.

## Backend responsibilities (current)

The backend (`backend/`) provides:
- Users: register/login
- Notebooks: CRUD + upload/download `.ipynb`
- Sharing: public + share-to-user-by-email

## Next milestones (suggested)

- Add **teams/projects**: notebooks grouped into projects
- Add **versioning**: keep notebook revisions instead of overwriting files
- Add **search**: full-text over notebook markdown cells + paper summaries
- Add **paper ingestion**: upload PDF → extract text → structured summary (can be a separate worker service)

