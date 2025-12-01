from flask import jsonify, request
import os
from openai import OpenAI
from dotenv import load_dotenv
import re

load_dotenv()

def validar_arquivo_audio():
    if 'audio' not in request.files:
        return False, "Arquivo de áudio não enviado", 400
    
    arquivo = request.files['audio']
    
    if arquivo.filename == '':
        return False, "Nenhum arquivo selecionado", 400
    
    extensoes_permitidas = {'.ogg', '.wav', '.mp3', '.m4a', '.webm'}
    nome_arquivo = arquivo.filename.lower()
    if not any(nome_arquivo.endswith(ext) for ext in extensoes_permitidas):
        return False, "Tipo de arquivo não suportado", 415

    arquivo.seek(0, os.SEEK_END)
    tamanho = arquivo.tell()
    arquivo.seek(0)
    
    if tamanho > 25 * 1024 * 1024:  
        return False, "Arquivo muito grande (máximo 25MB)", 413
    
    if tamanho == 0:
        return False, "Arquivo vazio", 400
    
    return True, arquivo, 200

def validar_chave_api():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key or api_key.strip() == "":
        return False, "API key não configurada", 500
    
    return True, api_key, 200