# Zhihuishu-Auto-QA

AI-Based Zhihuishu Auto QA Script

## Usage Instructions

First, install the required dependencies.

```sh
uv venv
.venv\Scripts\activate
uv sync
```

Complete the `secret.py.example` file with your API key for the platform you are using for `api_key`.\
Then copy or rename the file to `secret.py`.

We suggest U repsonse before ask questions bcs u cant response questions which was asked by yourself.

```bash
uv run .\main.py
```
