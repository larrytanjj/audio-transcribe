from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import os
import uuid
import sqlite3
import shutil
from pydantic import BaseModel

from transformers import WhisperProcessor, WhisperForConditionalGeneration
import torch
import librosa

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
DATABASE_FILE = "transcriptions.db"
UPLOAD_DIR = "uploads"

MODEL_NAME = "openai/whisper-tiny"
processor = WhisperProcessor.from_pretrained(MODEL_NAME)
model = WhisperForConditionalGeneration.from_pretrained(MODEL_NAME)
model.config.forced_decoder_ids = None
device = "cuda" if torch.cuda.is_available() else "cpu"
model = model.to(device)

class Transcription(BaseModel):
    original_filename: str
    unique_filename: str
    transcription: str

# Create uploads folder
os.makedirs(UPLOAD_DIR, exist_ok=True)

def init_db():
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()

    # Create table for transcriptions
    cursor.execute(
        """
    CREATE TABLE IF NOT EXISTS transcriptions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        original_filename TEXT NOT NULL,
        unique_filename TEXT NOT NULL,
        transcription TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """
    )
    conn.commit()
    conn.close()


init_db()

def get_unique_filename(original_filename: str) -> str:

    base_name, extension = os.path.splitext(original_filename)

    # Generate unique filename with UUID
    unique_filename = f"{base_name}_{uuid.uuid4().hex}{extension}"
    return unique_filename

#save the transcription into sqlite
def save_transcriptions(transcriptions):
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()

    try:
        cursor.execute(
            "INSERT INTO transcriptions (original_filename, unique_filename, transcription) VALUES (?, ?, ?)",
            (
                transcriptions.original_filename,
                transcriptions.unique_filename,
                transcriptions.transcription,
            ),
        )
        conn.commit()
        conn.close()
        return transcriptions
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="Already exists")
    
def transcribe_with_whisper(audio_path: str) -> str:
    try:
        # Load audio
        speech_array, sampling_rate = librosa.load(audio_path, sr=16000)
        
        # Process audio with Whisper processor
        input_features = processor(speech_array, sampling_rate=16000, return_tensors="pt").input_features
        input_features = input_features.to(device)
        
        # Generate token ids
        predicted_ids = model.generate(input_features)
        
        # Decode token ids to text
        transcription = processor.batch_decode(predicted_ids, skip_special_tokens=True)[0]
        
        return transcription
    except Exception as e:
        # Log the error and return an empty string if transcription fails
        print(f"Transcription error: {str(e)}")
        return f"Transcription failed: {str(e)}"

#Get health of backend
@app.get("/health")
def health():
    return {"status": "healthy", "service": "audio-transcribe", "version": "1.0.0"}

@app.post("/transcribe")
async def transcribe_audio(audio_file: UploadFile = File(...)):

    try:
        # Check if the file upload is a audio file
        content_type = audio_file.content_type
        if not content_type or not content_type.startswith("audio/"):
            raise HTTPException(
                status_code=400, detail="Uploaded file is not an audio file"
            )

        # Generate unique filename usind uuid
        original_filename = audio_file.filename
        unique_filename = get_unique_filename(original_filename)

        # Save the file
        file_path = os.path.join(UPLOAD_DIR, unique_filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(audio_file.file, buffer)

        transcription = transcribe_with_whisper(file_path)

        data = Transcription(
            original_filename=original_filename,
            unique_filename=unique_filename,
            transcription=transcription,
        )
        return save_transcriptions(data)
    except Exception as e:
        # close the file
        await audio_file.close()
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")
    finally:
        # close the file
        await audio_file.close()


@app.get("/transcriptions")
def get_all_transcriptions():
    conn = sqlite3.connect(DATABASE_FILE)
    conn.row_factory = sqlite3.Row 
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT * FROM transcriptions ORDER BY created_at DESC")
        rows = cursor.fetchall()
        
        # Convert rows to list of dictionaries
        transcriptions = []
        for row in rows:
            transcriptions.append({
                "id": row["id"],
                "original_filename": row["original_filename"],
                "unique_filename": row["unique_filename"],
                "transcription": row["transcription"],
                "created_at": row["created_at"]
            })
        
        return transcriptions
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        conn.close()


@app.get("/search")
def search(query: str = ""):
    conn = sqlite3.connect(DATABASE_FILE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    #Search by original filename
    try:
        sql_query = """
        SELECT * FROM transcriptions 
        WHERE original_filename LIKE ?
        ORDER BY created_at DESC
        """
        search_term = f"%{query}%"
        
        cursor.execute(sql_query, (search_term,))
        rows = cursor.fetchall()
        transcriptions = []
        for row in rows:
            transcriptions.append({
                "id": row["id"],
                "original_filename": row["original_filename"],
                "unique_filename": row["unique_filename"],
                "transcription": row["transcription"],
                "created_at": row["created_at"]
            })
        return transcriptions
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    finally:
        conn.close()


@app.delete("/transcriptions/{transcription_id}")
def delete_transcription(transcription_id: int):
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    try:
        #check if existing in db
        cursor.execute(
            "SELECT unique_filename FROM transcriptions WHERE id = ?",
            (transcription_id,)
        )
        result = cursor.fetchone()
        
        if result is None:
            raise HTTPException(status_code=404, detail=f"Transcription with ID {transcription_id} not found")
        
        #get the unique filename so can be deleted later
        unique_filename = result[0]
        file_path = os.path.join(UPLOAD_DIR, unique_filename)
        
        #delete from db
        cursor.execute(
            "DELETE FROM transcriptions WHERE id = ?",
            (transcription_id,)
        )
        
        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail=f"Transcription with ID {transcription_id} not found")
        
        conn.commit()
        
        try:
            #delete the actual audio file
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception as e:
            print(f"Error deleting file {file_path}: {str(e)}")
        
        return {
            "success": True,
            "message": f"Transcription with ID {transcription_id} deleted successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting transcription: {str(e)}")
    finally:
        conn.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)