# Prymal OS

AI "OS" - An orchestration framework for using agents to scale humans in an organization. Turn human ideas into AI work.

## Project Structure

```
app.py              - Main Flask application entry point
templates/
  index.html        - Main HTML template
static/
  css/style.css     - Application styles
  js/main.js        - Client-side JavaScript
requirements.txt    - Python dependencies
```

## Stack

- **Language**: Python 3.11
- **Web Framework**: Flask
- **Production Server**: Gunicorn
- **CORS**: flask-cors

## Running the App

Development:
```bash
python app.py
```

Production:
```bash
gunicorn --bind=0.0.0.0:5000 --reuse-port app:app
```

The app runs on port 5000.

## API Endpoints

- `GET /` - Main landing page
- `GET /api/health` - Health check endpoint

## Deployment

Configured for Replit autoscale deployment using Gunicorn.
