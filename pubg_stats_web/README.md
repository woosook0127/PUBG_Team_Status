# PUBG Stats Viewer

A Flask web application to view PUBG player statistics using the official PUBG API.

## Features (Planned)

- View player season stats (K/D, wins, damage, etc.).
- Analyze performance across different game modes.
- Display weapon proficiency.
- Show recent match history.
- Visualize data with charts.

## Setup

### Prerequisites

- Python 3.8+
- pip

### Installation

1.  **Clone the repository:**
    ```bash
    git clone <repository_url>
    cd pubg_stats_web
    ```

2.  **Create a virtual environment (recommended):**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Set up Environment Variables:**

    You need a PUBG API key to use this application.
    -   Go to the [PUBG Developer Portal](https://developer.pubg.com/) and register for an API key.
    -   Once you have your API key, create a `.env` file in the `pubg_stats_web` root directory by copying the example file:
        ```bash
        cp .env.example .env
        ```
    -   Open the `.env` file and replace `your_api_key_here` with your actual API key:
        ```
        PUBG_API_KEY=your_actual_api_key_here
        ```

## Running the Application

1.  **Ensure your virtual environment is activated.**
2.  **Run the Flask development server:**
    ```bash
    python app.py
    ```
3.  Open your web browser and go to `http://127.0.0.1:5000/`.

## Project Structure

```
/pubg_stats_web/
├── app.py             # Main Flask application
├── static/            # For CSS, JS, images
│   ├── css/style.css
│   ├── js/script.js
│   └── images/
├── templates/         # For HTML templates
│   └── index.html
├── services/          # For PUBG API interaction logic
│   ├── __init__.py
│   └── pubg_api.py
├── utils/             # For utility functions
│   ├── __init__.py
│   └── helpers.py
├── .env.example       # Example for environment variables
├── requirements.txt   # Python dependencies
└── README.md          # Project description
```

## API Endpoints (Planned)

-   `GET /`: Renders the main page.
-   `GET /api/seasons`: Fetches available PUBG seasons.
-   `GET /api/player_stats?player_name=<name>&season_id=<id>`: Fetches player stats for a given season.
    (More to be added)

## Contributing

Contributions are welcome! Please fork the repository and submit a pull request.
(Further contribution guidelines can be added here).

## License

This project is licensed under the MIT License - see the LICENSE file for details (if one is added).
Not affiliated with PUBG Corporation or KRAFTON, Inc.
```
