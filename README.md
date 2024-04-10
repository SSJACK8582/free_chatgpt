# Free ChatGPT
Utilize the unlimited free GPT-3.5-Turbo API service provided by the login-free ChatGPT Web
# Deploy
```bash
pip install -r requirements.txt
python main.py
```
# Example
```
curl --location 'http://127.0.0.1:5000/v1/chat/completions' \
--header 'Content-Type: application/json' \
--data '{
    "messages": [
        {
            "role": "user",
            "content": "hello"
        }
    ]
}'
```
