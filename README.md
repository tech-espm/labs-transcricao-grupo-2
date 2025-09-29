# Laboratório Experimental - Sistemas de Informação ESPM

<p align="center">
    <a href="https://www.espm.br/cursos-de-graduacao/sistemas-de-informacao/"><img src="https://raw.githubusercontent.com/tech-espm/misc-template/main/logo.png" alt="Sistemas de Informação ESPM" style="width: 375px;"/></a>
</p>

# Transcrição de Áudio por IA

### 2025-02

## Integrantes
- [Luzivania de Jesus Bonfim](https://github.com/bonfim1)
- [Maria Gabriela Vieira dos Santos](https://github.com/mgabriel4)
- [Mateus Carnevale Colmeal](https://github.com/colmeal)

## Cliente do Projeto

ESPM

## Descrição do Projeto

---

### 🎙️ Transcrição e Tradução de Áudio com OpenAI

Este projeto mostra como *converter fala em texto* usando a API da OpenAI. Ele possui duas funções principais:

* *Transcrição* 📝 → transforma a fala em texto no *mesmo idioma do áudio*.

  * Exemplo: áudio em português → texto em português.

* *Tradução* 🌍 → transforma a fala em texto *traduzido para o inglês*.

  * Exemplo: áudio em português → texto em inglês.

---

#### 📂 Estrutura do Projeto


📁 projeto-audio
 ┣ 📄 main.py        # Código principal (transcrição + tradução)
 ┣ 📄 audio.ogg      # Arquivo de áudio de exemplo
 ┣ 📄 .env           # Variáveis de ambiente (chave da API)
 ┗ 📄 README.md      # Documentação


---

#### ⚙️ Pré-requisitos

* Python 3.9 ou superior
* Biblioteca oficial openai
* Biblioteca python-dotenv para ler variáveis do .env

Instale as dependências:

```bash
pip install openai python-dotenv
```

---

#### 🔑 Configuração da chave de API

Crie um arquivo *.env* na raiz do projeto com sua chave:

```env
OPENAI_API_KEY=sua_chave_aqui
```

> ⚠️ Importante: nunca compartilhe sua chave de API em repositórios públicos.

---

#### ▶️ Como executar

1. Coloque seu arquivo de áudio na raiz do projeto, por exemplo audio.ogg.
2. Rode o script no terminal:

   ```bash
   python main.py
   ```

3. A saída no terminal mostrará:

   * *Transcrição:* texto no idioma original do áudio.
   * *Tradução:* texto traduzido para o inglês.

---

#### 🔎 Como funciona o fluxo

1. O usuário fornece um arquivo de áudio (ex.: audio.ogg).
2. O script em Python envia o áudio para a API da OpenAI.
3. A API processa:

   * Se for *transcrição*, retorna o texto no mesmo idioma.
   * Se for *tradução*, retorna o texto em inglês.
4. O script imprime os resultados no terminal.

---

#### 📊 Diagrama simplificado

```mermaid flowchart LR

    A[Usuário] --> B[Arquivo de Áudio]
    B --> C[Script Python]
    C -->|API OpenAI| D[Transcrição]
    C -->|API OpenAI| E[Tradução]
    D --> F[Texto Original]
    E --> G[Texto em Inglês]

```
---
#### 📌 Observações

* O arquivo de áudio pode estar em formatos comuns: .ogg, .mp3, .wav.
* Modelos usados:

  * *gpt-4o-transcribe* → para transcrição.
  * *whisper-1* → para tradução.
* Útil para criar legendas, anotações de reuniões, ou traduzir entrevistas.

---

# Licença

Este projeto é licenciado sob a [MIT License](https://github.com/tech-espm/labs-transcricao-grupo-2/blob/main/LICENSE).

<p align="right">
    <a href="https://www.espm.br/cursos-de-graduacao/sistemas-de-informacao/"><img src="https://raw.githubusercontent.com/tech-espm/misc-template/main/logo-si-512.png" alt="Sistemas de Informação ESPM" style="width: 375px;"/></a>
</p>
