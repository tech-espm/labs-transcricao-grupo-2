# 🎙️ API – Upload, Transcrição e Tradução de Áudio

Este projeto permite fazer upload de áudios, transcrevê-los para texto e traduzir para outros idiomas. Este documento está focado em falar dos endpoints futuros deste projeto.

## 🚀 Endpoints da API

1. Upload de Áudio
**POST /upload**

Descrição: Faz o upload de um arquivo de áudio para o servidor.

Entrada:

Tipo: multipart/form-data

Campo: file → arquivo de áudio (.ogg, .mp3, .wav).

Resposta:

{
  "file_id": "123abc",
  "file_path": "media/uploads/audio.ogg",
  "message": "Upload realizado com sucesso"
}

2. Transcrição de Áudio
**POST /transcrever**

Descrição: Transcreve o áudio enviado anteriormente.

Entrada:

{
  "file_id": "123abc"
}


Resposta:

{
  "file_id": "123abc",
  "transcription": "Olá, este é um exemplo de transcrição."
}

3. Tradução de Texto

**POST /traduzir**

Descrição: Traduz a transcrição para o idioma especificado.

Entrada:

{
  "file_id": "123abc",
  "text": "Olá, este é um exemplo de transcrição.",
  "target_lang": "en"
}

Resposta:

{
  "file_id": "123abc",
  "translated_text": "Hello, this is a sample transcription."
}

## 📲 Fluxo no Front-end

O usuário faz upload do áudio → chama POST /upload.

O front obtém o file_id e chama POST /transcrever.

Opcionalmente, o front chama POST /traduzir para obter a tradução.

## 💻 Exemplo de Uso no Front-end (JavaScript)

``` python

    // Upload de áudio
    async function uploadAudio(file) {
    const formData = new FormData();
    formData.append("file", file);

    const response = await fetch("/upload", {
        method: "POST",
        body: formData
    });

    return await response.json();
    }

    // Transcrever áudio
    async function transcrever(fileId) {
    const response = await fetch("/transcrever", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ file_id: fileId })
    });

    return await response.json();
    }

    // Traduzir transcrição
    async function traduzir(fileId, text, lang) {
    const response = await fetch("/traduzir", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ file_id: fileId, text, target_lang: lang })
    });

    return await response.json();
    }
```