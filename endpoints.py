from flask import Flask, render_template, json, request, Response, session, redirect, url_for, jsonify
from datetime import datetime, timedelta
import config
from werkzeug.exceptions import HTTPException
import os

app = Flask(__name__)
app.secret_key = 'dev'
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/')
def index():
    hoje = datetime.today().strftime('%Y-%m-%d')
    return render_template('index/index.html', hoje=hoje)

# Endpoint para upload de áudio
@app.route('/upload-audio', methods=['POST'])
def upload_audio():
    if 'audio' not in request.files:
        return jsonify({'error': 'No audio file provided'}), 400
    file = request.files['audio']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    filepath = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(filepath)

    return jsonify({'message': 'File uploaded successfully', 'filepath': filepath}), 200

if __name__ == '__main__':
    app.run(host=config.host, port=config.port, debug=True)