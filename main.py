from fastapi import FastAPI, HTTPException, Depends, UploadFile, File
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from typing import List
import os
import shutil

DATABASE_URL = "postgresql://postgres:root@localhost/vulnerable_Test"  # Update with your credentials

# Create the database engine
engine = create_engine(DATABASE_URL)

# Create a configured "Session" class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create a Base class for the models
Base = declarative_base()

# Define the Event model
class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    organization = Column(String, index=True)
    severity = Column(String, index=True)
    status = Column(String)

# Define the Music model
class Music(Base):
    __tablename__ = "music"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String)
    filepath = Column(String)

# Create the tables in the database
Base.metadata.create_all(bind=engine)

# Initialize FastAPI app
app = FastAPI()

# Pydantic model for Event creation
class EventCreate(BaseModel):
    organization: str
    severity: str
    status: str

# Pydantic model for Music creation
class MusicCreate(BaseModel):
    filename: str

# Dependency to get the database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Endpoint to insert event data
@app.post("/events/", response_model=EventCreate)
def create_event(event: EventCreate, db: Session = Depends(get_db)):
    db_event = Event(**event.dict())
    db.add(db_event)
    db.commit()
    db.refresh(db_event)
    return db_event
from pathlib import Path
# Endpoint to insert music data
# Directory to store uploaded music files
UPLOAD_DIRECTORY = "./uploaded_music"
Path(UPLOAD_DIRECTORY).mkdir(parents=True, exist_ok=True)

@app.post("/music/", response_model=MusicCreate)
async def create_music(file: UploadFile = File(...), db: Session = Depends(get_db)):
    if file.content_type != "audio/mpeg":
        raise HTTPException(status_code=400, detail="Only MP3 audio files are allowed")

    # Generate a unique file path
    file_path = os.path.join(UPLOAD_DIRECTORY, file.filename)
    
    # Save the file on disk
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Store metadata in the database
    db_music = Music(filename=file.filename, filepath=file_path)
    db.add(db_music)
    db.commit()
    db.refresh(db_music)
    
    return db_music

# Endpoint to fetch all events
@app.get("/events/", response_model=List[EventCreate])
def read_events(db: Session = Depends(get_db)):
    events = db.query(Event).all()
    return events

# Endpoint to fetch a specific event by ID
@app.get("/events/{event_id}", response_model=EventCreate)
def read_event(event_id: int, db: Session = Depends(get_db)):
    event = db.query(Event).filter(Event.id == event_id).first()
    if event is None:
        raise HTTPException(status_code=404, detail="Event not found")
    return event

# Endpoint to fetch all music files
@app.get("/music/", response_model=List[MusicCreate])
def read_music(db: Session = Depends(get_db)):
    music_files = db.query(Music).all()
    return music_files

# Run FastAPI server with uvicorn
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
