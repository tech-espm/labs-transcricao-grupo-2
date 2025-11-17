from flask import Flask, render_template, request, jsonify
from datetime import datetime
import openai
import os
import config
import tempfile
import traceback
import uuid
from metricas import registrar_upload_valido, registrar_processamento, taxa_sucesso_24h, resumo_24h, metricas_endpoint
from validador import validar_arquivo_audio, validar_chave_api

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY') or os.urandom(24)
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
AUDIO_MODEL = os.getenv("AUDIO_MODEL", "gpt-4o-transcribe")
TEXT_MODEL = os.getenv("TEXT_MODEL", "gpt-4o-mini")

UPLOAD_FOLDER = 'media/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

ARQUIVOS = {}

@app.route('/')
def index():
    hoje = datetime.today().strftime('%Y-%m-%d')
    return render_template('index/index.html', hoje=hoje)

@app.route('/upload-audio', methods=['POST'])
def upload_audio():
    """
    Faz upload e processa imediatamente a transcrição do áudio.
    """
    sucesso, resultado, status_code = validar_arquivo_audio()
    if not sucesso:
        return jsonify({"error": resultado}), status_code

    arquivo = resultado
    registrar_upload_valido()

    try:
        caminho_arquivo = os.path.join(UPLOAD_FOLDER, arquivo.filename)
        arquivo.save(caminho_arquivo)

        from openai import OpenAI
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        with open(caminho_arquivo, "rb") as f:
            transcription = client.audio.transcriptions.create(model=AUDIO_MODEL, file=f)
        texto = transcription.text

        with open(caminho_arquivo + ".txt", "w", encoding="utf-8") as f:
            f.write(texto)

        registrar_processamento(True)
        return jsonify({
            "message": "Processado com sucesso",
            "filepath": caminho_arquivo,
            "text": texto
        }), 200

    except Exception as e:
        registrar_processamento(False)
        return jsonify({"error": f"Falha no processamento: {str(e)}"}), 500

@app.route('/upload', methods=['POST'])
def upload():
    """Upload simples (sem processamento)."""
    ok, result, status = validar_arquivo_audio()
    if not ok:
        return jsonify({"error": result}), status

    arquivo = result
    file_id = str(uuid.uuid4())
    caminho_arquivo = os.path.join(UPLOAD_FOLDER, f"{file_id}_{arquivo.filename}")
    arquivo.save(caminho_arquivo)

    ARQUIVOS[file_id] = caminho_arquivo
    registrar_upload_valido()

    return jsonify({
        "file_id": file_id,
        "file_path": caminho_arquivo,
        "message": "Upload realizado com sucesso"
    }), 200

@app.route('/transcrever', methods=['POST'])
def transcrever():
    """Transcreve um arquivo já enviado via /upload."""
    dados = request.get_json()
    file_id = dados.get("file_id")

    if not file_id or file_id not in ARQUIVOS:
        return jsonify({"error": "Arquivo não encontrado"}), 404

    caminho = ARQUIVOS[file_id]

    try:
        with open(caminho, "rb") as f:
            transcription = client.audio.transcriptions.create(model=AUDIO_MODEL, file=f)

        registrar_processamento(True)
        return jsonify({
            "file_id": file_id,
            "transcription": transcription.text
        }), 200

    except Exception as e:
        registrar_processamento(False)
        return jsonify({"error": str(e)}), 500


def _translate_text(texto_src: str, target_lang: str) -> str:
    if not target_lang or target_lang.lower() in ("en", "en-us", "english"):
        return texto_src

    prompt = (
        "Traduza o texto a seguir para o idioma alvo com máxima fidelidade, "
        "mantendo nomes próprios e termos técnicos. "
        f"Idioma alvo: {target_lang}\n\n"
        f"Texto:\n{texto_src}"
    )

    resp = client.chat.completions.create(
        model=TEXT_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )
    return resp.choices[0].message.content.strip()


@app.route('/traduzir', methods=['POST'])
def traduzir():
    """Traduz texto transcrito."""
    dados = request.get_json()
    file_id = dados.get("file_id")
    texto = dados.get("text")
    target_lang = dados.get("target_lang", "en")

    if not texto:
        return jsonify({"error": "Texto não fornecido"}), 400

    try:
        traducao = _translate_text(texto, target_lang)
        registrar_processamento(True)
        return jsonify({
            "file_id": file_id,
            "translated_text": traducao
        }), 200
    except Exception as e:
        registrar_processamento(False)
        return jsonify({"error": str(e)}), 500

@app.route('/translate-audio', methods=['POST'])
def translate_audio():
    ok_key, msg_key, _ = validar_chave_api()
    if not ok_key:
        return jsonify({"error": msg_key}), 500

    ok_file, result_file, status = validar_arquivo_audio()
    if not ok_file:
        return jsonify({"error": result_file}), status
    arquivo = result_file

    target_language = request.form.get("target_language", "pt-BR")
    registrar_upload_valido()

    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(arquivo.filename)[1]) as tmp:
            arquivo.save(tmp.name)
            temp_path = tmp.name

        with open(temp_path, "rb") as f:
            translation = client.audio.translations.create(model=AUDIO_MODEL, file=f)

        english_text = getattr(translation, "text", None) or translation
        final_text = _translate_text(english_text, target_language)

        registrar_processamento(True)

        return jsonify({
            "ok": True,
            "target_language": target_language,
            "text_en": english_text,
            "text": final_text
        }), 200

    except Exception as e:
        registrar_processamento(False)
        return jsonify({
            "ok": False,
            "error": f"Falha na tradução do áudio: {str(e)}",
            "trace": traceback.format_exc(limit=2)
        }), 500

    finally:
        try:
            if temp_path and os.path.exists(temp_path):
                os.remove(temp_path)
        except Exception:
            pass


@app.route('/healthz', methods=['GET'])
def healthz():
    taxa = taxa_sucesso_24h()
    dados = resumo_24h()
    dados["meta_alcancada"] = taxa >= 0.95
    status = 200 if dados["meta_alcancada"] else 503
    return jsonify(dados), status

@app.route('/metricas', methods=['GET'])
def metricas():
    return metricas_endpoint()

if __name__ == '__main__':
    app.run(host=config.host, port=config.port, debug=True)
