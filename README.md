# Audio Transcriber
This is a web application for transcribing audio files using the Whisper model from OpenAI.

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
- Build the Docker image for both backend and frontend
- Start the FastAPI application and React Web application

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

- `backend` - FastAPI application code
- `frontend` - ReactJS application code
- `docker-compose.yml` - Docker Compose configuration
- `setup.sh` - Setup script

## API Documentation

Once the service is running, you can view the Swagger UI documentation at:
http://localhost:8000/docs

## Technical Details

- The application uses the `whisper-tiny` model for transcription
- Audio files are stored in the `uploads` directory
- Transcription data is stored in a SQLite database
