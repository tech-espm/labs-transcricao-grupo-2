# endpoints.py
from flask import Flask, render_template, request, jsonify
from datetime import datetime
import os
import config
from metricas import registrar_upload_valido, registrar_processamento, taxa_sucesso_24h, resumo_24h, metrics_endpoint
from validador import validar_arquivo_audio, validar_chave_api

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY') or os.urandom(24)

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

@app.route('/metrics', methods=['GET'])
def metrics():
    return metrics_endpoint()

if __name__ == '__main__':
    app.run(host=config.host, port=config.port, debug=True)
