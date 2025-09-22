from flask import Flask, request, jsonify
from validador import validar_arquivo_audio, validar_chave_api
import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# Configurações
app.config['MAX_CONTENT_LENGTH'] = 25 * 1024 * 1024  # 25MB
UPLOAD_FOLDER = 'media/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/transcrever', methods=['POST'])
def transcrever_audio():
    """
    Endpoint para transcrição de áudio
    """
    # Validação do arquivo
    sucesso, resultado, status_code = validar_arquivo_audio()
    if not sucesso:
        return jsonify({"error": resultado}), status_code
    arquivo = resultado
    
    # Validação da API key
    sucesso, resultado, status_code = validar_chave_api()
    if not sucesso:
        return jsonify({"error": resultado}), status_code
    
    try:
        # Salva o arquivo temporariamente
        caminho_arquivo = os.path.join(UPLOAD_FOLDER, arquivo.filename)
        arquivo.save(caminho_arquivo)
        
        # Configura cliente OpenAI
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        # Processa o áudio
        with open(caminho_arquivo, "rb") as audio_file:
            transcription = client.audio.transcriptions.create(
                model="whisper-1", 
                file=audio_file,
                response_format="verbose_json"
            )
        
        # Limpa o arquivo temporário
        os.remove(caminho_arquivo)
        
        return jsonify({
            "texto": transcription.text,
            "segmentos": transcription.segments if hasattr(transcription, 'segments') else []
        }), 200
        
    except Exception as e:
        # Limpa o arquivo em caso de erro
        if os.path.exists(caminho_arquivo):
            os.remove(caminho_arquivo)
        
        return jsonify({
            "error": "Erro interno no processamento do áudio",
            "details": str(e)
        }), 500

@app.route('/traduzir', methods=['POST'])
def traduzir_audio():
    """
    Endpoint para tradução de áudio
    """
    # Validação do arquivo
    sucesso, resultado, status_code = validar_arquivo_audio()
    if not sucesso:
        return jsonify({"error": resultado}), status_code
    arquivo = resultado
    
    # Validação da API key
    sucesso, resultado, status_code = validar_chave_api()
    if not sucesso:
        return jsonify({"error": resultado}), status_code
    
    try:
        # Salva o arquivo temporariamente
        caminho_arquivo = os.path.join(UPLOAD_FOLDER, arquivo.filename)
        arquivo.save(caminho_arquivo)
        
        # Configura cliente OpenAI
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        # Processa a tradução
        with open(caminho_arquivo, "rb") as audio_file:
            translation = client.audio.translations.create(
                model="whisper-1", 
                file=audio_file
            )
        
        # Limpa o arquivo 
        os.remove(caminho_arquivo)
        
        return jsonify({
            "traducao": translation.text
        }), 200
        
    except Exception as e:
        # Limpa o arquivo em caso de erro
        if os.path.exists(caminho_arquivo):
            os.remove(caminho_arquivo)
        
        return jsonify({
            "error": "Erro interno na tradução do áudio",
            "details": str(e)
        }), 500

# erro
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