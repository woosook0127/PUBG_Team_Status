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

Once the setup is complete, you can run the FastAPI application using Uvicorn:

```bash
uvicorn app.main:app --reload
```

The application will typically be available at `http://127.0.0.1:8000`.
You can access the UI at `http://127.0.0.1:8000/ui/index.html`.
API documentation (Swagger UI) will be at `http://127.0.0.1:8000/docs`.

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
