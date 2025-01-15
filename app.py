import requests
import json

class LlamaAgent:
    def __init__(self, api_key, base_url, system_message=""):
        self.api_key = api_key
        self.base_url = base_url
        self.system_message = system_message
        self.conversation = [{"role": "system", "content": self.system_message}] if self.system_message else []

    def send_message(self, user_message):
        # Add user message to the conversation
        self.conversation.append({"role": "user", "content": user_message})

        # Prepare the payload
        payload = {
            "messages": self.conversation,
            "model": "Meta-Llama-3-8B-Instruct",
        }

        # Make the POST request to the Llama API
        try:
            response = requests.post(
                f"{self.base_url}/v1/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json=payload,
            )
            response.raise_for_status()  # Raise HTTPError for bad responses (4xx and 5xx)
        except requests.exceptions.RequestException as e:
            return f"Error: {e}"

        # Parse the response
        data = response.json()
        if "choices" in data and len(data["choices"]) > 0:
            assistant_message = data["choices"][0]["message"]["content"]
            self.conversation.append({"role": "assistant", "content": assistant_message})
            return assistant_message
        else:
            return "Error: No response from the server."

# Main logic for the chat interface
def main():
    print("Welcome to the Stock Analysis Assistant!")
    print("Type 'exit' to end the chat.\n")

    api_key = "llama"  # Your API key
    base_url = "http://127.0.0.1:8080"  # Your local server address
    system_message = (
        "You are a financial assistant specializing in stock market analysis. "
        "Provide accurate and detailed insights based on user queries."
    )

    agent = LlamaAgent(api_key, base_url, system_message)

    while True:
        user_input = input("You: ").strip()
        if user_input.lower() == "exit":
            print("Goodbye!")
            break

        response = agent.send_message(user_input)
        print(f"Assistant: {response}")

# Entry point
if __name__ == "__main__":
    main()
