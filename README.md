# llama_ReACT-agents
Used llama 3 8b model to create reasoning agents 


This repository contains four Python files that implement different variations of an AI-powered chat system using the Llama model API, with features for stock analysis, file processing, and web browsing capabilities.

## Table of Contents
- [Overview](#overview)
- [Files Description](#files-description)
  - [app.py](#apppy)
  - [file_agent.py](#file_agentpy)
  - [liveagent.py](#liveagentpy)
  - [stock_agent.py](#stock_agentpy)
- [Setup and Installation](#setup-and-installation)
- [Usage](#usage)
- [API Keys and Dependencies](#api-keys-and-dependencies)
- [Features](#features)

## Overview

This project implements various AI-powered chat interfaces that combine the capabilities of the Llama language model with additional features such as stock market analysis, file processing, and live web browsing. Each file represents a different implementation with specific features and use cases.

## Files Description

### app.py

A basic implementation of the Llama chat interface with stock analysis capabilities.

**Key Features:**
- Basic chat interface using command line
- Integration with Llama API
- System message customization
- Simple conversation history management

**Usage:**
```python
python app.py
```

**Implementation Details:**
- Uses a `LlamaAgent` class for handling chat functionality
- Maintains conversation history
- Supports system messages for context
- Simple command-line interface for interaction

### file_agent.py

A FastAPI-based web application that handles file uploads and chat functionality with a modern UI.

**Key Features:**
- File upload support (.txt files)
- WebSocket-based chat interface
- Modern web UI using Tailwind CSS
- Chat history management
- Integration with Ollama API

**Implementation Details:**
- FastAPI backend with async support
- HTML/JavaScript frontend with drag-and-drop file upload
- Real-time chat updates
- Error handling and logging
- File content analysis using AI

**API Endpoints:**
- `/upload/`: Handles file uploads
- `/chat/`: Processes chat messages
- `/history/`: Retrieves chat history
- `/`: Serves the main HTML interface

### liveagent.py

An advanced implementation combining stock analysis, web browsing, and document retrieval capabilities.

**Key Features:**
- Live stock data fetching using Alpha Vantage API
- Web browsing capabilities using Selenium
- Document retrieval system
- Caching mechanism for performance
- Flask-based web interface

**Key Components:**
- Stock data retrieval and caching
- Live web browsing with Selenium
- Document retrieval system
- Flask web server with modern UI
- Real-time chat functionality

**Implementation Details:**
- Uses Selenium for web scraping
- Implements caching for better performance
- Combines multiple data sources
- Advanced error handling
- Responsive web interface

### stock_agent.py

A focused implementation for stock market analysis with Llama model integration.

**Key Features:**
- Real-time stock data fetching
- Integration with Alpha Vantage API
- Basic chat capabilities
- Stock symbol detection
- Command-line interface

**Implementation Details:**
- Dedicated stock data retrieval
- Symbol detection algorithm
- Error handling for API limits
- Formatted stock information output
- Simple conversation management

## Setup and Installation

1. Install required dependencies:
```bash
pip install fastapi uvicorn requests beautifulsoup4 selenium flask flask-cors aiohttp
```

2. Set up API keys:
- Llama API key
- Alpha Vantage API key (for stock data)

3. Configure Chrome WebDriver (for liveagent.py):
- Install Chrome browser
- Download ChromeDriver matching your Chrome version
- Add ChromeDriver to system PATH

## Usage

### Basic Chat (app.py):
```bash
python app.py
```

### File Processing Server (file_agent.py):
```bash
uvicorn file_agent:app --reload
```

### Live Agent (liveagent.py):
```bash
python liveagent.py
```

### Stock Analysis (stock_agent.py):
```bash
python stock_agent.py
```

## API Keys and Dependencies

Required API Keys:
- Llama API key for AI model access
- Alpha Vantage API key for stock data

Main Dependencies:
- `requests`: HTTP requests
- `fastapi`: Web framework
- `flask`: Web framework
- `selenium`: Web browsing
- `beautifulsoup4`: Web scraping
- `aiohttp`: Async HTTP
- `uvicorn`: ASGI server

## Features

### Common Features Across Files:
- AI-powered chat capabilities
- Conversation history management
- Error handling
- API integration

### Specialized Features:
- File upload and processing
- Stock market data analysis
- Live web browsing
- Document retrieval
- Caching mechanisms
- Modern web interfaces

### Security Notes:
- API keys should be stored securely
- Input validation is implemented
- Error handling for API failures
- Rate limiting consideration for external APIs

This project demonstrates various approaches to building AI-powered chat applications with different specialized features and implementations.

