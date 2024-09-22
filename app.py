from flask import Flask, request, render_template, jsonify
from speechmatics.models import ConnectionSettings
from speechmatics.batch_client import BatchClient
from httpx import HTTPStatusError
import os

app = Flask(__name__)

API_KEY = "P2JLrpyQtwQTtYzKsLZjeNCIbwAYGXdM"  # Replace with your actual Speechmatics API key
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'wav', 'mp3', 'ogg'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def transcribe_audio(file_path):
    settings = ConnectionSettings(
        url="https://asr.api.speechmatics.com/v2",
        auth_token=API_KEY,
    )
    
    conf = {
        "type": "transcription",
        "transcription_config": {
            "language": "fa"  # Persian language code
        }
    }
    
    with BatchClient(settings) as client:
        try:
            job_id = client.submit_job(
                audio=file_path,
                transcription_config=conf,
            )
            transcript = client.wait_for_completion(job_id, transcription_format='txt')
            return transcript
        except HTTPStatusError as e:
            if e.response.status_code == 401:
                return 'Invalid API key'
            elif e.response.status_code == 400:
                return e.response.json()['detail']
            else:
                raise e

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        if 'file' not in request.files:
            return jsonify({'error': 'No file part'})
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No selected file'})
        if file and allowed_file(file.filename):
            filename = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            file.save(filename)
            transcript = transcribe_audio(filename)
            os.remove(filename)  # Remove the file after transcription
            return jsonify({'transcript': transcript})
    return render_template('upload.html')

if __name__ == '__main__':
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    app.run(debug=True)