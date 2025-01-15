# app.py
from fastapi import FastAPI, UploadFile, File, WebSocket, HTTPException
from fastapi.responses import HTMLResponse
import json
import aiohttp
import asyncio
from pathlib import Path
import uvicorn
from typing import Dict, List
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Store chat history in memory (you might want to use a database in production)
chat_history: List[Dict] = []

# Ollama API endpoint
OLLAMA_API = "http://localhost:11434/api/generate"

async def process_with_ollama(prompt: str) -> str:
    """Send a prompt to Ollama and get the response"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                OLLAMA_API,
                json={
                    "model": "phi4",
                    "prompt": prompt,
                    "stream": False
                }
            ) as response:
                if response.status != 200:
                    raise HTTPException(status_code=500, detail="Ollama API error")
                data = await response.json()
                return data.get("response", "")
    except Exception as e:
        logger.error(f"Error processing with Ollama: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/upload/")
async def upload_file(file: UploadFile = File(...)):
    """Handle file uploads"""
    if not file.filename.endswith('.txt'):
        raise HTTPException(status_code=400, detail="Only .txt files are supported")
    
    try:
        content = await file.read()
        text = content.decode('utf-8')
        
        # Process file content with Ollama
        prompt = f"I'm sharing a text file with you. Please analyze its content and provide a summary:\n\n{text[:4000]}"
        response = await process_with_ollama(prompt)
        
        # Add to chat history
        chat_history.extend([
            {"role": "user", "content": f"Uploaded file: {file.filename}"},
            {"role": "assistant", "content": response}
        ])
        
        return {"message": "File processed successfully", "response": response}
    except Exception as e:
        logger.error(f"Error processing file: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/chat/")
async def chat(message: Dict):
    """Handle chat messages"""
    try:
        user_message = message.get("message", "")
        response = await process_with_ollama(user_message)
        
        # Add to chat history
        chat_history.extend([
            {"role": "user", "content": user_message},
            {"role": "assistant", "content": response}
        ])
        
        return {"response": response}
    except Exception as e:
        logger.error(f"Error in chat: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/history/")
async def get_history():
    """Get chat history"""
    return {"history": chat_history}

# HTML template
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Chat with Phi-4</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        .chat-container { height: calc(100vh - 180px); }
    </style>
</head>
<body class="bg-gray-100">
    <div class="container mx-auto max-w-4xl p-4">
        <h1 class="text-2xl font-bold text-center mb-2">Chat with Phi-4</h1>
        <p class="text-center text-gray-600 mb-4">Drop files or type messages to chat</p>
        
        <!-- Chat messages -->
        <div id="chat-container" class="bg-white rounded-lg p-4 mb-4 chat-container overflow-y-auto">
            <div id="messages"></div>
        </div>

        <!-- Error display -->
        <div id="error" class="hidden text-red-500 mb-4"></div>
        
        <!-- Input area -->
        <div class="relative">
            <input type="text" id="message-input" 
                   class="w-full p-4 pr-24 rounded-lg border border-gray-300 focus:outline-none focus:border-blue-500"
                   placeholder="Type a message or drop a file...">
            <div class="absolute right-2 top-2 flex space-x-2">
                <label class="w-10 h-10 flex items-center justify-center bg-gray-100 rounded-lg cursor-pointer hover:bg-gray-200">
                    <input type="file" id="file-input" accept=".txt" class="hidden">
                    <svg class="w-5 h-5 text-gray-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12"/>
                    </svg>
                </label>
                <button id="send-button" 
                        class="w-10 h-10 flex items-center justify-center bg-blue-500 text-white rounded-lg disabled:bg-gray-300">
                    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/>
                    </svg>
                </button>
            </div>
        </div>
    </div>

    <script>
        const messagesDiv = document.getElementById('messages');
        const messageInput = document.getElementById('message-input');
        const sendButton = document.getElementById('send-button');
        const fileInput = document.getElementById('file-input');
        const errorDiv = document.getElementById('error');

        // Load chat history
        async function loadHistory() {
            try {
                const response = await fetch('/history/');
                const data = await response.json();
                data.history.forEach(message => addMessage(message));
            } catch (error) {
                showError('Error loading chat history');
            }
        }

        function addMessage(message) {
            const messageDiv = document.createElement('div');
            messageDiv.className = `flex ${message.role === 'user' ? 'justify-end' : 'justify-start'} mb-4`;
            
            const content = document.createElement('div');
            content.className = `p-3 rounded-lg ${
                message.role === 'user' ? 'bg-blue-500 text-white' : 'bg-gray-200 text-gray-800'
            }`;
            content.textContent = message.content;
            
            messageDiv.appendChild(content);
            messagesDiv.appendChild(messageDiv);
            messagesDiv.scrollTop = messagesDiv.scrollHeight;
        }

        function showError(message) {
            errorDiv.textContent = message;
            errorDiv.classList.remove('hidden');
            setTimeout(() => errorDiv.classList.add('hidden'), 5000);
        }

        async function sendMessage(message) {
            try {
                const response = await fetch('/chat/', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({message})
                });
                const data = await response.json();
                addMessage({role: 'assistant', content: data.response});
            } catch (error) {
                showError('Error sending message');
            }
        }

        // Handle file uploads
        fileInput.addEventListener('change', async (e) => {
            const file = e.target.files[0];
            if (!file) return;
            
            const formData = new FormData();
            formData.append('file', file);
            
            try {
                const response = await fetch('/upload/', {
                    method: 'POST',
                    body: formData
                });
                const data = await response.json();
                addMessage({role: 'user', content: `Uploaded file: ${file.name}`});
                addMessage({role: 'assistant', content: data.response});
            } catch (error) {
                showError('Error uploading file');
            }
        });

        // Handle send button
        sendButton.addEventListener('click', () => {
            const message = messageInput.value.trim();
            if (!message) return;
            
            addMessage({role: 'user', content: message});
            sendMessage(message);
            messageInput.value = '';
        });

        // Handle Enter key
        messageInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                sendButton.click();
            }
        });

        // Handle drag and drop
        document.body.addEventListener('dragover', (e) => {
            e.preventDefault();
            e.stopPropagation();
        });

        document.body.addEventListener('drop', async (e) => {
            e.preventDefault();
            e.stopPropagation();
            
            const file = e.dataTransfer.files[0];
            if (!file || !file.name.endsWith('.txt')) {
                showError('Please drop a valid text file');
                return;
            }
            
            const formData = new FormData();
            formData.append('file', file);
            
            try {
                const response = await fetch('/upload/', {
                    method: 'POST',
                    body: formData
                });
                const data = await response.json();
                addMessage({role: 'user', content: `Uploaded file: ${file.name}`});
                addMessage({role: 'assistant', content: data.response});
            } catch (error) {
                showError('Error uploading file');
            }
        });

        // Load history on page load
        loadHistory();
    </script>
</body>
</html>
"""

@app.get("/")
async def get_html():
    """Serve the HTML page"""
    return HTMLResponse(HTML_TEMPLATE)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)