# PUBG Stats Dashboard

A FastAPI web application that provides player statistics, team identification, and performance comparison for PlayerUnknown's Battlegrounds (PUBG). It wraps the official PUBG API, adding caching and processed data views.

## Features

*   **Individual Weapon Stats:** Displays a player's top weapon in primary categories (AR, SR, DMR, SMG, Shotgun) for a given season, including total damage, kills, and calculated Damage Per Match (DPM).
*   **Team Identification:** Identifies a player's primary team (clan or frequent squad) based on recent match history analysis and clan membership.
*   **Team Performance Comparison:** For an identified team, displays radar charts for each teammate, showing their average Kills, Damage, Survival Time, Assists, and a normalized Placement Score when playing with the main player.
*   **Overall Team Stats:** Calculates and displays aggregated statistics (Avg. Team Kills, Damage, Survival Time, Match Rank) for the identified team when they play together as a full unit.
*   **Caching:** Implements in-memory caching for responses from the external PUBG API to improve performance and reduce API call volume.
*   **Interactive UI:** A web interface built with HTML, CSS, and JavaScript (using Chart.js for radar charts) to input player details and view stats.

## Tech Stack

*   **Backend:** Python, FastAPI, Uvicorn
*   **HTTP Client:** HTTPX (for asynchronous API calls)
*   **Rate Limiting:** aiolimiter
*   **Caching:** aiocache
*   **Frontend:** HTML, CSS, JavaScript, Chart.js
*   **Containerization:** Docker

## Project Structure

```
.
├── app/                    # Main application module
│   ├── __init__.py
│   ├── cache_utils.py      # Caching configuration (aiocache)
│   ├── exceptions.py       # Custom API exceptions
│   ├── main.py             # FastAPI application, endpoints
│   ├── pubg_api.py         # Wrapper for official PUBG API calls
│   ├── team_analyzer.py    # Logic for team identification
│   ├── team_performance.py # Logic for calculating team stats
│   └── weapon_utils.py     # Utilities for weapon categorization, platform mapping
├── static/                 # Frontend static files (HTML, CSS, JS)
│   ├── index.html
│   ├── script.js
│   └── style.css
├── tests/                  # Pytest unit tests
│   ├── __init__.py
│   ├── test_pubg_api.py
│   ├── test_team_analyzer.py
│   ├── test_team_performance.py
│   └── test_weapon_utils.py
├── .env.example            # Example environment variables
├── Dockerfile              # Docker configuration
├── MANUAL_TESTING_GUIDE.md # Guide for manual testing
├── README.md               # This file
└── requirements.txt        # Python dependencies
```

## Setup and Running Locally

### Prerequisites

*   Python 3.9+
*   pip

### Installation

1.  **Clone the repository:**
    ```bash
    git clone <repository_url>
    cd <repository_name>
    ```

2.  **Create a virtual environment (recommended):**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Set up environment variables:**
    *   Copy `.env.example` to a new file named `.env`:
        ```bash
        cp .env.example .env
        ```
    *   Open the `.env` file and replace `"YOUR_PUBG_API_KEY_HERE"` with your actual PUBG API key. You can obtain one from the [Official PUBG Developer Portal](https://developer.pubg.com/).
        ```env
        PUBG_API_KEY="your_actual_api_key"
        ```

### Running Locally

Once the general setup (cloning, API key in `.env`) is complete, you can run the FastAPI application using Uvicorn. Below are instructions for a standard Python virtual environment and a Conda environment on Linux.

**Using a Standard Python Virtual Environment (venv):**

This is covered by the steps above (creating `venv`, activating, `pip install`). To run the server:
```bash
# Ensure your venv is activated: source venv/bin/activate
# Ensure PUBG_API_KEY is set in your .env file or exported in your shell
uvicorn app.main:app --reload
```
The application will typically be available at `http://127.0.0.1:8000`.

**Using a Linux with Conda Environment:**

These instructions are for running the server on a Linux machine using a Conda environment.

1.  **Create and Activate Conda Environment:**
    *   Create a new Conda environment (e.g., named `pubg_stats_env`) with Python 3.10 (or your preferred compatible version):
        ```bash
        conda create -n pubg_stats_env python=3.10 -y
        ```
    *   Activate the newly created environment:
        ```bash
        conda activate pubg_stats_env
        ```

2.  **Install Dependencies:**
    *   Navigate to the project root directory (where `requirements.txt` is located).
    *   Install the required packages using pip within your Conda environment:
        ```bash
        pip install -r requirements.txt
        ```

3.  **Set API Key Environment Variable:**
    *   The application requires the `PUBG_API_KEY` to be set. You can do this in several ways on Linux:
        *   **For the current session:**
            ```bash
            export PUBG_API_KEY="your_actual_api_key"
            ```
            Replace `"your_actual_api_key"` with your key. You'll need to do this every time you open a new terminal session.
        *   **For persistence across sessions (recommended):** Add the export line to your shell's configuration file (e.g., `~/.bashrc` if you use bash, or `~/.zshrc` if you use zsh).
            ```bash
            echo 'export PUBG_API_KEY="your_actual_api_key"' >> ~/.bashrc 
            # For zsh, use ~/.zshrc
            source ~/.bashrc # Or source ~/.zshrc, or open a new terminal
            ```
        *   **Using a `.env` file (if you prefer Uvicorn to pick it up via a helper or if you run a script):** While the application directly uses `os.getenv()`, if you place your `PUBG_API_KEY` in a `.env` file in the project root (as described in the general setup), some Uvicorn launch methods or helper scripts might load it. However, `export` or shell profile is more standard for Conda environments unless `python-dotenv` is explicitly used in the run script.

4.  **Run the Uvicorn Server:**
    *   From the project root directory (inside your activated Conda environment, with the API key exported or available), run Uvicorn:
        ```bash
        uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
        ```
        *   `--host 0.0.0.0`: This makes the server accessible from other devices on your local network.
        *   `--port 8000`: Specifies the port.
        *   `--reload`: Enables auto-reload for development. Remove this for production deployments.

### Accessing the Application

*   **From the machine running the server:**
    *   UI: `http://localhost:8000/ui/index.html` or `http://127.0.0.1:8000/ui/index.html`
    *   API Docs (Swagger): `http://localhost:8000/docs` or `http://127.0.0.1:8000/docs`

*   **From another machine (e.g., Windows) on the same local network:**
    *   If the server was started with `--host 0.0.0.0` (as in the Conda/Docker examples), you can access the UI from another device.
    *   Find the local IP address of the Linux machine running the server. You can usually find this by running `ip addr show` or `hostname -I` in the Linux terminal.
    *   On your Windows machine (or other device), open a web browser and go to:
        `http://<LINUX_MACHINE_IP_ADDRESS>:8000/ui/index.html`
        (Replace `<LINUX_MACHINE_IP_ADDRESS>` with the actual IP, e.g., `http://192.168.1.105:8000/ui/index.html`).

## Deployment with Docker

This application can be easily containerized and run using Docker.

### Prerequisites

*   Docker installed and running.

### Building the Docker Image

1.  Ensure you have a `.env` file in the project root with your `PUBG_API_KEY`, as described in the "Setup and Running Locally" section. While the `.env` file itself is not copied into the image for security, it's used by the `docker run` command below. Alternatively, you can pass the environment variable directly.

2.  From the project root directory (where the `Dockerfile` is located), build the Docker image:
    ```bash
    docker build -t pubg-stats-dashboard .
    ```
    (You can replace `pubg-stats-dashboard` with your preferred image name).

### Running the Docker Container

You need to provide the `PUBG_API_KEY` environment variable to the container when running it.

**Method 1: Using `--env-file` (Recommended if you have a `.env` file):**

Ensure your `.env` file in the project root has the `PUBG_API_KEY` defined:
```
PUBG_API_KEY="your_actual_api_key_from_pubg_developer_portal"
```

Then run the container:
```bash
docker run -d -p 8000:8000 --env-file .env pubg-stats-dashboard
```

*   `-d`: Runs the container in detached mode (in the background).
*   `-p 8000:8000`: Maps port 8000 of the host to port 8000 of the container.
*   `--env-file .env`: Loads environment variables from the `.env` file.
*   `pubg-stats-dashboard`: The name of the image you built.

**Method 2: Using `-e` to pass the environment variable directly:**

```bash
docker run -d -p 8000:8000 -e PUBG_API_KEY="your_actual_api_key_from_pubg_developer_portal" pubg-stats-dashboard
```

Replace `"your_actual_api_key_from_pubg_developer_portal"` with your actual API key.

### Accessing the Application

Once the container is running, the application will be accessible:

*   **UI:** `http://localhost:8000/ui/index.html`
*   **API Docs (Swagger):** `http://localhost:8000/docs`

## Running Tests

Unit tests are written using `pytest`.

1.  Ensure you have installed development dependencies (including `pytest` and `pytest-asyncio` from `requirements.txt`).
2.  From the project root directory, run:
    ```bash
    pytest
    ```
    For more verbose output:
    ```bash
    pytest -v
    ```

## Manual Testing

Refer to the `MANUAL_TESTING_GUIDE.md` for detailed manual test cases covering various features of the application.

## Future Enhancements / Considerations

*   **Advanced Caching:** Switch from `SimpleMemoryCache` to Redis or Memcached for a more robust and scalable caching solution in a multi-instance deployment.
*   **Teammate Name Resolution:** Fetch and display player names for teammate account IDs in the team performance sections (requires additional API calls and careful rate limit management).
*   **Season ID Handling:** Implement a more dynamic way to fetch or suggest current/valid season IDs for users, as these change over time.
*   **More Detailed Stats:** Expand the range of statistics displayed (e.g., headshot ratios, specific damage types, survival stats beyond time).
*   **UI/UX Improvements:**
    *   Graphing trends over time.
    *   More interactive chart elements.
    *   User accounts or saved player searches.
*   **Production Uvicorn Settings:** Use Gunicorn as a process manager for Uvicorn in a production Docker environment for better scalability and management (e.g., `gunicorn -w 4 -k uvicorn.workers.UvicornWorker app.main:app`).
*   **CI/CD Pipeline:** Set up automated testing and deployment.
```
