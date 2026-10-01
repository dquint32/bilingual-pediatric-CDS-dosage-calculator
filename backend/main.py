"""Entry point: ``uvicorn main:app`` or ``python main.py`` (from the backend folder)."""

from cds.api import app

__all__ = ["app"]

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
