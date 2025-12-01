from flask import Flask, request, jsonify
from validador import validar_arquivo_audio, validar_chave_api
import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

app.config['MAX_CONTENT_LENGTH'] = 25 * 1024 * 1024  # 25MB
UPLOAD_FOLDER = 'media/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/transcrever', methods=['POST'])
def transcrever_audio():
    sucesso, resultado, status_code = validar_arquivo_audio()
    if not sucesso:
        return jsonify({"error": resultado}), status_code
    arquivo = resultado

    sucesso, resultado, status_code = validar_chave_api()
    if not sucesso:
        return jsonify({"error": resultado}), status_code
    
    try:
        caminho_arquivo = os.path.join(UPLOAD_FOLDER, arquivo.filename)
        arquivo.save(caminho_arquivo)
        
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
        with open(caminho_arquivo, "rb") as audio_file:
            transcription = client.audio.transcriptions.create(
                model="whisper-1", 
                file=audio_file,
                response_format="verbose_json"
            )
        
        os.remove(caminho_arquivo)
        
        return jsonify({
            "texto": transcription.text,
            "segmentos": transcription.segments if hasattr(transcription, 'segments') else []
        }), 200
        
    except Exception as e:
        if os.path.exists(caminho_arquivo):
            os.remove(caminho_arquivo)
        
        return jsonify({
            "error": "Erro interno no processamento do áudio",
            "details": str(e)
        }), 500

@app.route('/traduzir', methods=['POST'])
def traduzir_audio():
    sucesso, resultado, status_code = validar_arquivo_audio()
    if not sucesso:
        return jsonify({"error": resultado}), status_code
    arquivo = resultado
    
    sucesso, resultado, status_code = validar_chave_api()
    if not sucesso:
        return jsonify({"error": resultado}), status_code
    
    try:
        caminho_arquivo = os.path.join(UPLOAD_FOLDER, arquivo.filename)
        arquivo.save(caminho_arquivo)
        
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        with open(caminho_arquivo, "rb") as audio_file:
            translation = client.audio.translations.create(
                model="whisper-1", 
                file=audio_file
            )
        
        os.remove(caminho_arquivo)
        
        return jsonify({
            "traducao": translation.text
        }), 200
        
    except Exception as e:
        if os.path.exists(caminho_arquivo):
            os.remove(caminho_arquivo)
        
        return jsonify({
            "error": "Erro interno na tradução do áudio",
            "details": str(e)
        }), 500

@app.errorhandler(413)
def muito_grande(e):
    return jsonify({"error": "Arquivo muito grande (máximo 25MB)"}), 413

@app.errorhandler(400)
def bad_request(e):
    return jsonify({"error": "Requisição inválida"}), 400

@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Endpoint não encontrado"}), 404

@app.errorhandler(500)
def internal_error(e):
    return jsonify({"error": "Erro interno do servidor"}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)