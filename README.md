# Audio Transcription API

This is a FastAPI-based service for transcribing audio files using the Whisper model from OpenAI.

## Features

- Upload audio files for transcription
- List all transcriptions
- Search transcriptions by filename
- Delete transcriptions

## Prerequisites

- Docker
- Docker Compose

## Setup and Running

1. Clone this repository
2. Make the setup script executable:
   ```bash
   chmod +x setup.sh
   ```
3. Run the setup script:
   ```bash
   ./setup.sh
   ```

This will:
- Create necessary directories
- Build the Docker image
- Start the FastAPI application

## API Endpoints

- `GET /health` - Check API health
- `POST /transcribe` - Upload an audio file for transcription
- `GET /transcriptions` - Get all transcriptions
- `GET /search?query=<search_term>` - Search transcriptions by filename
- `DELETE /transcriptions/{transcription_id}` - Delete a transcription

## Manual Docker Commands

If you prefer to run the commands manually:

1. Build the Docker image:
   ```bash
   docker-compose build
   ```

2. Start the service:
   ```bash
   docker-compose up -d
   ```

3. Stop the service:
   ```bash
   docker-compose down
   ```

## Project Structure

- `main.py` - FastAPI application code
- `Dockerfile` - Docker configuration
- `docker-compose.yml` - Docker Compose configuration
- `requirements.txt` - Python dependencies
- `uploads/` - Directory for audio file storage
- `transcriptions.db` - SQLite database for transcriptions

## API Documentation

Once the service is running, you can view the Swagger UI documentation at:
http://localhost:8000/docs

## Technical Details

- The application uses the `whisper-tiny` model for transcription
- Audio files are stored in the `uploads` directory
- Transcription data is stored in a SQLite database
