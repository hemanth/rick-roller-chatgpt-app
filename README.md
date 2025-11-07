# rickroller-chatgpt-app
> This app exposes a single tool with a widget that plays the classic Rick Astley video.

https://github.com/user-attachments/assets/a76b05b5-0d70-4bd5-9f96-e006ecb2ad65


## Prerequisites

- Python 3.10+
- A virtual environment (recommended)

## Installation

```bash
cd rickroller-chatgpt-app
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
```

## Run the server

```bash
python main.py
```

Server runs on `http://localhost:8000`.

## Tool and widget

- Tool identifier: `rick-roll`
- Resource/template URI: `ui://widget/rick-roll.html`

When the tool is invoked, it returns widget metadata and an embedded resource containing HTML with an iframe pointing to `https://www.youtube.com/embed/dQw4w9WgXcQ`.

### Optional input

```json
{
  "autoplay": true
}
```

Note: browsers often block autoplay unless muted or user-initiated.

## Testing

- Use MCP Inspector to connect to `http://localhost:8000/mcp` and list tools/resources.
- Invoke `rick-roll` with or without `autoplay`.

