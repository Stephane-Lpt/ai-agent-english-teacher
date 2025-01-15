from fastapi import FastAPI, File, UploadFile
from fastapi.responses import StreamingResponse
import shutil
import os
import io
from script import stream_graph_updates
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO Replace "*" with the frontend URL for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Temporary directory to store files
temp_dir = "back/temp_files/"
os.makedirs(temp_dir, exist_ok=True)


@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.post("/process-audio/")
async def process_audio(file: UploadFile = File(...)):
    """
    Endpoint that takes a .wav audio file, processes it, and returns another .wav file.
    """
    # if file.content_type != "audio/wav" or file.content_type != "audio/mpeg":
    #     return {"error": "The file must be in .wav or .mp3 format"}

    # Temporary save of the input file
    input_file_path = os.path.join(temp_dir, file.filename)
    with open(input_file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # test input_file_path = temp_dir + "hello-role.wav"

    output_audio_data = stream_graph_updates(input_file_path)

    # Convert the audio data (bytes) to a file-like object (in-memory file)
    audio_stream = io.BytesIO(output_audio_data)

    # Return the in-memory audio stream
    # TODO: Need to add the transcription of the ai generated audio and also user audio transcription after asr
    return StreamingResponse(audio_stream, media_type="audio/wav", headers={"Content-Disposition": f"attachment; filename=processed_hello-role.wav"})



# Automatic cleanup of temporary files (additional cron task or other management can be added)
@app.on_event("shutdown")
def cleanup_temp_files():
    shutil.rmtree(temp_dir)
