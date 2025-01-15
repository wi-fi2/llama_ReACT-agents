import requests

class LlamaAgent:
    def __init__(self, api_key, base_url, stock_api_key, system_message=""):
        self.api_key = api_key
        self.base_url = base_url
        self.stock_api_key = stock_api_key
        self.system_message = system_message
        self.conversation = [{"role": "system", "content": self.system_message}] if self.system_message else []

    def get_stock_data(self, symbol):
        """
        Fetch stock data using Alpha Vantage API.
        """
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
                return (
                    f"Stock: {symbol}\n"
                    f"Time: {latest_time}\n"
                    f"Open: {stock_info['1. open']}\n"
                    f"High: {stock_info['2. high']}\n"
                    f"Low: {stock_info['3. low']}\n"
                    f"Close: {stock_info['4. close']}\n"
                    f"Volume: {stock_info['5. volume']}\n"
                )
            elif "Note" in data:
                return "API request limit reached. Please wait a while before trying again."
            else:
                return "No stock data found for the provided symbol."
        else:
            return f"Error: Unable to fetch stock data (HTTP {response.status_code})."

    def send_message(self, user_message):
        """
        Handles user input, processes stock-related queries, and queries the Llama model for other inputs.
        """
        if "stock" in user_message.lower() or "price" in user_message.lower():
            # Extract stock symbol from user query
            words = user_message.split()
            for word in words:
                if word.isupper() and len(word) <= 5:  # Likely a stock symbol (e.g., AAPL, TSLA)
                    return self.get_stock_data(word)
            return "Please provide a valid stock symbol (e.g., TSLA, AAPL)."

        # Query the Llama model for non-stock inputs
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

# Initialize the agent
if __name__ == "__main__":
    agent = LlamaAgent(
        api_key="llama",  # Your Llama API key
        base_url="http://127.0.0.1:8080",  # Your Llama server base URL
        stock_api_key="TJJ1TG11IJD0E9RF",  # Replace with your Alpha Vantage API key
        system_message="You are a stock analysis assistant that also helps with general queries.",
    )

    print("Welcome to the Stock Analysis Assistant!")
    print("Type 'exit' to end the chat.\n")

    while True:
        user_input = input("You: ")
        if user_input.lower() == "exit":
            print("Goodbye!")
            break
        response = agent.send_message(user_input)
        print(f"Assistant: {response}")
