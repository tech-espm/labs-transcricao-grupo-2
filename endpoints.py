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
from langdetect import detect


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
   Faz upload e transcrição do áudio (fluxo padronizado com gravação).
   """
   sucesso, arquivo, status_code = validar_arquivo_audio()
   if not sucesso:
       return jsonify({"error": arquivo}), status_code


   registrar_upload_valido()


   try:
       # salvar arquivo no diretório de uploads
       caminho_arquivo = os.path.join(UPLOAD_FOLDER, arquivo.filename)
       arquivo.save(caminho_arquivo)


       # transcrever áudio
       with open(caminho_arquivo, "rb") as f:
           transcription = client.audio.transcriptions.create(
               model=AUDIO_MODEL,
               file=f
           )
      
       texto = transcription.text


       registrar_processamento(True)


       # resposta padrão compatível com gravação
       return jsonify({
           "ok": True,
           "filepath": caminho_arquivo,
           "text_original": texto
       }), 200


   except Exception as e:
       registrar_processamento(False)
       return jsonify({
           "ok": False,
           "error": f"Falha no processamento: {str(e)}"
       }), 500


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
   # se o destino é inglês mas o texto já é inglês → não traduz
   if target_lang.lower().startswith("en"):
       try:
           idioma_atual = detect(texto_src)
           if idioma_atual == "en":
               return texto_src
       except:
           pass  # se falhar, ignora e traduz normalmente


   prompt = (
       f"Traduza o texto a seguir para {target_lang}:\n\n{texto_src}"
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
   """
   Novo fluxo correto:
   1) Transcreve o áudio usando gpt-4o-transcribe
   2) Traduz o texto usando modelo de texto (gpt-4o-mini)
   """


   # 1) valida chave
   ok_key, msg_key, _ = validar_chave_api()
   if not ok_key:
       return jsonify({"error": msg_key}), 500


   # 2) valida arquivo
   ok_file, result_file, status = validar_arquivo_audio()
   if not ok_file:
       return jsonify({"error": result_file}), status


   arquivo = result_file
   target_language = request.form.get("target_language", "en")


   registrar_upload_valido()


   temp_path = None
   try:
       # 3) salva arquivo temporário
       with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(arquivo.filename)[1]) as tmp:
           arquivo.save(tmp.name)
           temp_path = tmp.name


       # 4) transcrição do áudio — AGORA É ASSIM
       with open(temp_path, "rb") as f:
           transcription = client.audio.transcriptions.create(
               model=AUDIO_MODEL,  # gpt-4o-transcribe
               file=f
           )


       original_text = transcription.text


       # 5) Se o destino for inglês, já está pronto.
       if target_language.lower().startswith("en"):
           try:
               idioma_atual = detect(original_text)
               if idioma_atual != "en":
                   translated_text = _translate_text(original_text, "en")
               else:
                   translated_text = original_text
           except:
               translated_text = _translate_text(original_text, "en")


       else:
           # 6) tradução via modelo de texto
           prompt = (
               f"Traduza o texto a seguir para '{target_language}' com precisão alta.\n\n"
               f"Texto:\n{original_text}"
           )


           resp = client.chat.completions.create(
               model=TEXT_MODEL,
               messages=[{"role": "user", "content": prompt}],
               temperature=0
           )


           translated_text = resp.choices[0].message.content.strip()


       registrar_processamento(True)


       # 7) retorno final
       return jsonify({
           "ok": True,
           "target_language": target_language,
           "text_original": original_text,
           "text_translated": translated_text
       }), 200


   except Exception as e:
       registrar_processamento(False)
       return jsonify({
           "ok": False,
           "error": str(e),
           "trace": traceback.format_exc()
       }), 500


   finally:
       if temp_path and os.path.exists(temp_path):
           os.remove(temp_path)




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
