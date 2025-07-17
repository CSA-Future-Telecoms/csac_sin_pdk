# Sample Photonics PDK 0.0.0

Based on Cornestone PDK

## Installation

We recommend `uv`

```bash
# On macOS and Linux.
curl -LsSf https://astral.sh/uv/install.sh | sh
```

```bash
# On Windows.
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### Installation for users

Use python 3.11, 3.12 or 3.13. We recommend [VSCode](https://code.visualstudio.com/) as an IDE.

```
uv pip install csac_sin_pdk --upgrade
```

Then you need to restart Klayout to make sure the new technology installed appears.

### Installation for contributors


Then you can install with:

```bash
git clone https://github.com/gdsfactory/csac_sin_pdk.git
cd csac_sin_pdk
uv venv --python 3.12
uv sync --extra docs --extra dev
```

## Documentation

- [gdsfactory docs](https://gdsfactory.github.io/gdsfactory/)
