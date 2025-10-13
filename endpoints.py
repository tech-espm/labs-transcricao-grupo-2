# endpoints.py
from flask import Flask, render_template, request, jsonify
from datetime import datetime
import openai
import os
import config
import tempfile
import traceback
from metricas import registrar_upload_valido, registrar_processamento, taxa_sucesso_24h, resumo_24h, metricas_endpoint
from validador import validar_arquivo_audio, validar_chave_api

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY') or os.urandom(24)
client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
AUDIO_MODEL = os.getenv("AUDIO_MODEL", "gpt-4o-transcribe")  # ou "whisper-1"
TEXT_MODEL  = os.getenv("TEXT_MODEL",  "gpt-4o-mini")

UPLOAD_FOLDER = 'media/uploads'  # padroniza com outros scripts
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/')
def index():
    hoje = datetime.today().strftime('%Y-%m-%d')
    return render_template('index/index.html', hoje=hoje)

@app.route('/upload-audio', methods=['POST'])
def upload_audio():
    """
    Endpoint de upload + processamento (exemplo)
    Regras de métricas:
      - Se arquivo não é válido (faltando, extensão errada, etc.) -> NÃO conta na taxa.
      - Se é válido, registramos 'upload válido'; depois tentamos processar;
        - Se processar OK -> registrar_processamento(True)
        - Se der erro de processamento -> registrar_processamento(False)
    """
    # 1) Validação (NÃO conta na taxa se falhar aqui)
    sucesso, resultado, status_code = validar_arquivo_audio()
    if not sucesso:
        return jsonify({"error": resultado}), status_code

    arquivo = resultado  # o objeto de arquivo validado

    # 2) Upload é válido → registra
    registrar_upload_valido()

    # 3) Salva arquivo e processa
    try:
        caminho_arquivo = os.path.join(UPLOAD_FOLDER, arquivo.filename)
        arquivo.save(caminho_arquivo)

        # ==== PROCESSAMENTO ====
        # Coloque aqui seu fluxo real de processamento.
        # Exemplo mínimo: apenas "simular" sucesso (substitua pelo transcrever/traduzir etc.)
        # Caso use OpenAI, chame seu cliente aqui. Se ocorrer exceção, cai no except.
       
        from openai import OpenAI
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        with open(caminho_arquivo, "rb") as f:
            transcription = client.audio.transcriptions.create(model="gpt-4o-transcribe", file=f)
        texto = transcription.text
        
        with open(caminho_arquivo + ".txt", "w", encoding="utf-8") as f:
            f.write(texto)
        
        # Sucesso no processamento
        registrar_processamento(True)
        return jsonify({"message": "Processado com sucesso", "filepath": caminho_arquivo}), 200

    except Exception as e:
        # Falha no processamento (após upload válido)
        registrar_processamento(False)
        return jsonify({"error": f"Falha no processamento: {str(e)}"}), 500

# --- Saúde da aplicação baseada na meta (>= 95% nas últimas 24h) ---
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

def _translate_text(texto_src: str, target_lang: str) -> str:
    """
    Usa um modelo de texto para traduzir 'texto_src' ao idioma 'target_lang'.
    """
    if not target_lang or target_lang.lower() in ("en", "en-us", "english"):
        return texto_src  # já está em inglês

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


@app.route('/translate-audio', methods=['POST'])
def translate_audio():
    """
    Tradução de áudio:
      - Passos:
        1) validar arquivo (não conta na taxa se inválido)
        2) registrar upload válido
        3) salvar temporariamente e chamar audio.translations (áudio -> inglês)
        4) se 'target_language' != en, traduzimos o texto em um 2º passo
        5) registrar sucesso/erro no processamento (conta na taxa)
    """
    # 0) valida chave/api etc. (opcional)
    ok_key, msg_key, _ = validar_chave_api()
    if not ok_key:
        return jsonify({"error": msg_key}), 500

    # 1) valida o arquivo de áudio (NÃO conta na taxa se falhar aqui)
    ok_file, result_file, status = validar_arquivo_audio()
    if not ok_file:
        return jsonify({"error": result_file}), status
    arquivo = result_file

    # pega idioma alvo (padrão pt-BR para seu caso)
    target_language = request.form.get("target_language", "pt-BR")

    # 2) upload válido → registra
    registrar_upload_valido()

    temp_path = None
    try:
        # 3) salvar temporariamente
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(arquivo.filename)[1]) as tmp:
            arquivo.save(tmp.name)
            temp_path = tmp.name

        # 4) tradução do áudio → inglês (audio.translations)
        # Observação: translations retorna inglês por padrão.
        with open(temp_path, "rb") as f:
            translation = client.audio.translations.create(
                model=AUDIO_MODEL,
                file=f
                # Dica: você pode passar response_format="verbose_json" para metadados
            )

        english_text = getattr(translation, "text", None) or translation  # SDK retorna .text

        # 5) se alvo não for inglês, traduzimos o texto
        final_text = _translate_text(english_text, target_language)

        # 6) registrar sucesso no processamento
        registrar_processamento(True)

        return jsonify({
            "ok": True,
            "target_language": target_language,
            "text_en": english_text,
            "text": final_text
        }), 200

    except Exception as e:
        # 7) registrar falha no processamento
        registrar_processamento(False)
        return jsonify({
            "ok": False,
            "error": f"Falha na tradução do áudio: {str(e)}",
            "trace": traceback.format_exc(limit=2)
        }), 500

    finally:
        # 8) limpeza do arquivo temp
        try:
            if temp_path and os.path.exists(temp_path):
                os.remove(temp_path)
        except Exception:
            pass

if __name__ == '__main__':
    app.run(host=config.host, port=config.port, debug=True)
