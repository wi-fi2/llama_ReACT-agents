from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import time
import threading

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# LlamaAgent class
class LlamaAgent:
    def __init__(self, api_key, base_url, stock_api_key, retrieval_url, system_message=""):
        self.api_key = api_key
        self.base_url = base_url
        self.stock_api_key = stock_api_key
        self.retrieval_url = retrieval_url
        self.system_message = system_message
        self.conversation = [{"role": "system", "content": self.system_message}] if self.system_message else []

        # Set up Selenium for live web browsing
        self.chrome_options = Options()
        self.chrome_options.add_argument("--headless")  # Run in headless mode
        self.chrome_options.add_argument("--disable-gpu")
        self.chrome_options.add_argument("--no-sandbox")
        self.chrome_options.add_argument("--disable-dev-shm-usage")
        self.driver = webdriver.Chrome(service=Service(), options=self.chrome_options)

        # Cache for stock data and web search results
        self.stock_cache = {}
        self.web_cache = {}

    def get_stock_data(self, symbol):
        """
        Fetch stock data using Alpha Vantage API with caching.
        """
        if symbol in self.stock_cache:
            return self.stock_cache[symbol]

        url = f"https://www.alphavantage.co/query"
        params = {
            "function": "TIME_SERIES_INTRADAY",
            "symbol": symbol,
            "interval": "1min",
            "apikey": self.stock_api_key
        }
        response = requests.get(url, params=params)
        if response.status_code == 200:
            data = response.json()
            if "Time Series (1min)" in data:
                latest_time = list(data["Time Series (1min)"].keys())[0]
                stock_info = data["Time Series (1min)"][latest_time]
                result = (
                    f"Stock: {symbol}\n"
                    f"Time: {latest_time}\n"
                    f"Open: {stock_info['1. open']}\n"
                    f"High: {stock_info['2. high']}\n"
                    f"Low: {stock_info['3. low']}\n"
                    f"Close: {stock_info['4. close']}\n"
                    f"Volume: {stock_info['5. volume']}\n"
                )
                self.stock_cache[symbol] = result  # Cache the result
                return result
            elif "Note" in data:
                return "API request limit reached. Please wait a while before trying again."
            else:
                return "No stock data found for the provided symbol."
        else:
            return f"Error: Unable to fetch stock data (HTTP {response.status_code})."

    def retrieve_documents(self, query):
        """
        Retrieve relevant documents from the knowledge base using the retrieval service.
        """
        response = requests.post(
            self.retrieval_url,
            json={"query": query},
            headers={"Authorization": f"Bearer {self.api_key}"},
        )
        if response.status_code == 200:
            return response.json().get("documents", [])
        return []

    def browse_web_live(self, query):
        """
        Browse the web live using Selenium to fetch up-to-date information with caching.
        """
        if query in self.web_cache:
            return self.web_cache[query]

        try:
            # Use Google search to fetch live results
            search_url = f"https://www.google.com/search?q={query}"
            self.driver.get(search_url)
            time.sleep(1)  # Reduce wait time for faster responses

            # Extract search results
            results = self.driver.find_elements(By.CSS_SELECTOR, "div.g")
            snippets = []
            for result in results[:3]:  # Limit to top 3 results
                try:
                    title = result.find_element(By.CSS_SELECTOR, "h3").text
                    snippet = result.find_element(By.CSS_SELECTOR, "div.IsZvec").text
                    snippets.append(f"{title}: {snippet}")
                except:
                    continue

            if snippets:
                result = "\n".join(snippets)
                self.web_cache[query] = result  # Cache the result
                return result
            else:
                return "No live data found for the query."
        except Exception as e:
            return f"Error fetching live web data: {str(e)}"

    def send_message(self, user_message):
        """
        Handles user input, processes stock-related queries, retrieves documents, and browses the web live if needed.
        """
        if "stock" in user_message.lower() or "price" in user_message.lower():
            # Extract stock symbol from user query
            words = user_message.split()
            for word in words:
                if word.isupper() and len(word) <= 5:  # Likely a stock symbol (e.g., AAPL, TSLA)
                    return self.get_stock_data(word)
            return "Please provide a valid stock symbol (e.g., TSLA, AAPL)."

        # Check if the user wants to browse the web live
        if "browse" in user_message.lower() or "web" in user_message.lower():
            query = user_message.replace("browse", "").replace("web", "").strip()
            web_data = self.browse_web_live(query)
            if web_data:
                # Directly return the live web data without querying the model
                return f"Live Web Data:\n{web_data}"

        # Retrieve relevant documents for non-stock inputs
        documents = self.retrieve_documents(user_message)
        if documents:
            user_message += "\n\nRelevant Documents:\n" + "\n".join(documents)

        # Query the Llama model with the augmented input
        self.conversation.append({"role": "user", "content": user_message})
        payload = {"messages": self.conversation, "model": "Meta-Llama-3-8B-Instruct"}
        response = requests.post(
            f"{self.base_url}/v1/chat/completions",
            headers={"Authorization": f"Bearer {self.api_key}"},
            json=payload,
        )
        if response.status_code == 200:
            data = response.json()
            if "choices" in data and len(data["choices"]) > 0:
                assistant_message = data["choices"][0]["message"]["content"]
                self.conversation.append({"role": "assistant", "content": assistant_message})
                return assistant_message
        return "Error: Unable to fetch a response from the model."


# Initialize the LlamaAgent
agent = LlamaAgent(
    api_key="llama",  # Your Llama API key
    base_url="http://127.0.0.1:8080",  # Your Llama server base URL
    stock_api_key="TJJ1TG11IJD0E9RF",  # Replace with your Alpha Vantage API key
    retrieval_url="http://127.0.0.1:5000/retrieve",  # URL for the retrieval service
    system_message="You are a stock analysis assistant that also helps with general queries.",
)

# Flask routes
@app.route("/")
def home():
    """
    Serve the frontend webpage.
    """
    return render_template_string("""
   <!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Llama Agent Chat</title>
    <style>
        /* General Styles */
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 0;
            background-color: #f7f7f7;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
        }

        .chat-container {
            width: 100%;
            max-width: 800px;
            height: 90vh;
            background-color: #fff;
            border-radius: 12px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }

        .chat-header {
            background-color: #007bff;
            color: #fff;
            padding: 16px;
            text-align: center;
            font-size: 20px;
            font-weight: bold;
            border-top-left-radius: 12px;
            border-top-right-radius: 12px;
        }

        .chat-box {
            flex: 1;
            padding: 16px;
            overflow-y: auto;
            background-color: #fafafa;
            display: flex;
            flex-direction: column;
            gap: 12px;
        }

        .message {
            max-width: 70%;
            padding: 12px;
            border-radius: 12px;
            position: relative;
            animation: fadeIn 0.3s ease-in-out;
        }

        .user-message {
            background-color: #007bff;
            color: #fff;
            align-self: flex-end;
            border-bottom-right-radius: 4px;
        }

        .assistant-message {
            background-color: #e9ecef;
            color: #000;
            align-self: flex-start;
            border-bottom-left-radius: 4px;
        }

        .chat-input-container {
            display: flex;
            padding: 16px;
            background-color: #fff;
            border-top: 1px solid #ddd;
        }

        .chat-input {
            flex: 1;
            padding: 12px;
            border: 1px solid #ddd;
            border-radius: 8px;
            font-size: 16px;
            outline: none;
            transition: border-color 0.3s ease;
        }

        .chat-input:focus {
            border-color: #007bff;
        }

        .send-button {
            margin-left: 12px;
            padding: 12px 24px;
            background-color: #007bff;
            color: #fff;
            border: none;
            border-radius: 8px;
            font-size: 16px;
            cursor: pointer;
            transition: background-color 0.3s ease;
        }

        .send-button:hover {
            background-color: #0056b3;
        }

        /* Animations */
        @keyframes fadeIn {
            from {
                opacity: 0;
                transform: translateY(10px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
    </style>
</head>
<body>
    <div class="chat-container">
        <!-- Chat Header -->
        <div class="chat-header">
            Llama Agent Chat
        </div>

        <!-- Chat Box -->
        <div class="chat-box" id="chat-box">
            <!-- Messages will appear here dynamically -->
        </div>

        <!-- Chat Input -->
        <div class="chat-input-container">
            <input type="text" class="chat-input" id="user-input" placeholder="Type your message...">
            <button class="send-button" onclick="sendMessage()">Send</button>
        </div>
    </div>

    <script>
        // Function to send a message
        async function sendMessage() {
            const userInput = document.getElementById("user-input").value.trim();
            if (!userInput) return;

            // Add user message to the chat box
            const chatBox = document.getElementById("chat-box");
            const userMessage = document.createElement("div");
            userMessage.className = "message user-message";
            userMessage.textContent = userInput;
            chatBox.appendChild(userMessage);

            // Clear the input field
            document.getElementById("user-input").value = "";

            // Scroll to the bottom of the chat box
            chatBox.scrollTop = chatBox.scrollHeight;

            // Send the message to the backend
            try {
                const response = await fetch("/chat", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                    },
                    body: JSON.stringify({ message: userInput }),
                });

                if (!response.ok) {
                    throw new Error("Failed to fetch response");
                }

                const data = await response.json();
                const assistantMessage = document.createElement("div");
                assistantMessage.className = "message assistant-message";
                assistantMessage.textContent = data.response;
                chatBox.appendChild(assistantMessage);

                // Scroll to the bottom of the chat box
                chatBox.scrollTop = chatBox.scrollHeight;
            } catch (error) {
                console.error("Error:", error);
                const errorMessage = document.createElement("div");
                errorMessage.className = "message assistant-message";
                errorMessage.textContent = "Error: Unable to fetch response.";
                chatBox.appendChild(errorMessage);
            }
        }

        // Allow pressing Enter to send a message
        document.getElementById("user-input").addEventListener("keypress", function (e) {
            if (e.key === "Enter") {
                sendMessage();
            }
        });
    </script>
</body>
</html>
    """)


@app.route("/chat", methods=["POST"])
def chat():
    """
    Endpoint to handle user input and return the assistant's response.
    """
    data = request.json
    user_message = data.get("message")
    if not user_message:
        return jsonify({"error": "No message provided"}), 400

    response = agent.send_message(user_message)
    return jsonify({"response": response})


# Run the Flask app
if __name__ == "__main__":
    app.run(port=5000)  # Run the Flask app on port 5000