# TwinHunter

**TwinHunter** is a simple, clean, and extendable Windows desktop application to detect and delete duplicate images.

## Setup

1.  **Create a virtual environment:**
    ```bash
    python -m venv venv
    ```

2.  **Activate the virtual environment:**
    - Windows: `venv\Scripts\activate`

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

    > **Note:** If you get a "running scripts is disabled" error in PowerShell, run this command to allow script execution for your user:
    > ```powershell
    > Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
    > ```

## Running the App

```bash
python main.py
```
