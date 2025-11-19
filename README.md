# Zhihuishu-Auto-QA

AI-Based Zhihuishu Auto QA Script

## Installation

First, install the required dependencies.

```sh
uv venv
.venv\Scripts\activate
uv sync
```

## Configuration

### 1. API Key Configuration

Complete the `secret.py.example` file with your API key for the platform you are using for `api_key`.\
Then copy or rename the file to `secret.py`.

### 2. Platform Selection

The script supports two AI platforms: **deepseek** and **siliconflow**.

To switch platforms, edit `main.py` and modify line 65:

```python
provider = ["deepseek", "siliconflow"][0]  # 切换平台, 须在config.json文件中平台相关配置
```

- Use `[0]` for **deepseek**
- Use `[1]` for **siliconflow**

**Note:** Make sure the corresponding platform configuration exists in `config.json`. The default `config.json` includes configurations for both platforms:

```json
{
  "deepseek": {
    "base_url": "https://api.deepseek.com/v1",
    "model_name": "deepseek-chat"
  },
  "siliconflow": {
    "base_url": "https://api.siliconflow.cn/v1",
    "model_name": "deepseek-ai/DeepSeek-V3"
  }
}
```

## Usage

We suggest responding to questions before asking new ones, because you cannot respond to questions that were asked by yourself.

```bash
uv run .\main.py
```
