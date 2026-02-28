# Last SiX Hours

Automated YouTube content pipeline

For detailed specifications and design, refer to SPEC.md and DESIGN.md.

## Setup Instructions

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd viral_channel
   ```

2. Set up a virtual environment and install dependencies:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   pip install -r requirements.txt
   ```

3. Create an `.env` file based on the provided `.env.example` template and fill in your secrets:
   ```bash
   cp .env.example .env
   ```

4. Run the main application:
   ```bash
   python src/main.py
   ```

Ensure you have all necessary API keys and credentials configured in your `.env` file for YouTube, Telegram, Reddit, LLM, and TTS services.