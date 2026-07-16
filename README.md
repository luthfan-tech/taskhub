# SprintSync 🚀

SprintSync is a highly interactive, beautifully styled Developer Kanban & Sprint Board task manager contained entirely within a single Python file. It leverages an asynchronous FastAPI backend and a vanilla JavaScript frontend to deliver a seamless, zero-reload project management experience.

## ✨ Features

*   **Single-File Architecture:** The entire application (database schema, API endpoints, styling, and client-side logic) lives in `app.py`.
*   **Kanban Board Mechanics:** Three static columns (Backlog, Active Dev, QA/Completed) for straightforward task tracking.
*   **Native Drag & Drop:** Move cards effortlessly between columns using HTML5 Drag and Drop APIs, with instant background API updates.
*   **Live Telemetry Stats:** A dynamic header calculates and displays sprint velocity, total story points, and completed points in real time.
*   **Task Management:** Create, track, and delete tasks with attributes like Title, Description, Priority (High/Medium/Low), Story Points, and Assignee Initials.
*   **Dark UI Theme:** A gorgeous dark aesthetic powered by Tailwind CSS via CDN.
*   **High-Performance Database:** Uses async SQLAlchemy 2.0 and AIOSQLite with Write-Ahead Logging (WAL) enabled for rapid, non-blocking state changes.

## 🛠️ Tech Stack

*   **Backend:** Python, FastAPI, Uvicorn
*   **Database:** SQLite (aiosqlite), SQLAlchemy 2.0 (asyncio)
*   **Frontend:** HTML5, Vanilla JavaScript, Tailwind CSS (CDN)

## 🚀 Quickstart

### 1. Prerequisites
Ensure you have Python 3.8 or higher installed on your system.

### 2. Install Dependencies
Install the required Python packages using pip:

```bash
pip install fastapi uvicorn sqlalchemy aiosqlite

3. Run the Application
Save the provided code as app.py, then start the Uvicorn development server:

Bash
uvicorn app:app --reload
4. Open the Dashboard
Navigate to the following URL in your web browser:

Plaintext
[http://127.0.0.1:8000](http://127.0.0.1:8000)
Note: On its first run, SprintSync will automatically generate a local SQLite database file (sprintsync.db) and seed it with three demo tasks to get you started.

💻 Usage
Create a Task: Click the "CREATE TASK" button in the top right to open the modal and add a new item to your backlog.

Move a Task: Click and drag a task card from one column and drop it into another. The database updates automatically in the background.

Delete a Task: Hover over any task card and click the "DELETE" button in the top right corner of the card to permanently remove it.

Track Progress: Watch the telemetry bar at the top of the screen update automatically as you move tasks into the "QA / Completed" column.
