import sys
import requests
import json
import time
import os
from PyQt5.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QLineEdit, QPushButton, QWidget, QStatusBar, QMessageBox, QHBoxLayout, QDialog, QLabel)
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import QThread, pyqtSignal, QUrl, Qt # Corrected QThread, Qt

class WorkerThread(QThread):
    html_generated = pyqtSignal(str)
    error_occurred = pyqtSignal(str)

    def __init__(self, prompt, ls_api):
        super().__init__()
        self.prompt = prompt
        self.ls_api = ls_api
        self.api_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-05-20:generateContent"
        self.backoff_time = 2

    def run(self):
        max_retries = 4
        # --- IMPROVED PROMPT START ---
        user_message = f"""
Create a modern, responsive HTML website adhering strictly to **Material Design 3 principles**. The site should be based on the search query: "{self.prompt}".
**Key requirements:**
* **Content:** Integrate information and insights directly from the provided Google Search results. Ensure the content is informative, relevant, and well-structured with appropriate headings and paragraphs.
* **Layout:** Implement a clear, intuitive layout with a distinct header, a main content area, and a simple footer. Use Material Design 3 components where appropriate (e.g., cards for content blocks, elevated buttons, navigation elements).
* **Responsiveness:** Design for optimal viewing across all devices (mobile, tablet, desktop) using responsive techniques (e.g., flexbox/grid, media queries, Tailwind CSS responsive classes). The layout should adapt gracefully to different screen sizes.
* **Visuals:** Use high-quality **placeholder images** (e.g., `https://placehold.co/600x400/cccccc/ffffff?text=Image`) where appropriate, ensuring they fit the content contextually and have descriptive alt text.
* **Styling:** Use Tailwind CSS for all styling. Ensure rounded corners on all elements.
* **Ad-free:** The generated page must be completely free of advertisements or promotional content.
* **Font:** Use the 'Inter' font.

Provide only the HTML code, enclosed in ```html and ```. Do not include any conversational text or explanations outside the code block.
"""
        # --- IMPROVED PROMPT END ---

        for retry_count in range(max_retries):
            try:
                api_with_key = f"{self.api_url}?key={self.ls_api}"

                payload = {
                   "contents": [
                    {
                      "role": "user",
                      "parts": [
                         {"text": user_message}
                      ]
                    }
                   ],
                   "tools": [
                   {
                    "google_search": {}

                   }
                   ],
                   "safety_settings": [
                            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
                            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"}
                   ],
                   "generation_config": {
                       "temperature": 0.2,
                       "topK": 40,
                       "topP": 0.95
                   }
                }

                # Increased timeout to 60 seconds
                response = requests.post(api_with_key, json=payload, timeout=60)
                response.raise_for_status()

                result = response.json()

                if result.get("candidates") and result["candidates"][0].get("content") and result["candidates"][0]["content"].get("parts"):
                    html_text = result["candidates"][0]["content"]["parts"][0]["text"]

                    if html_text.startswith("```html") and html_text.endswith("```"):
                        html_text = html_text.strip("`html").strip("`").strip()

                        self.html_generated.emit(html_text)
                        return
                    else:
                        self.error_occurred.emit("AI response was empty or malformed.")
                        return
                else:
                    self.error_occurred.emit("AI response was empty or malformed.")
                    return

            except requests.exceptions.RequestException as e:
                if retry_count < max_retries - 1:
                    time.sleep(self.backoff_time)
                    self.backoff_time *= 2
                else:
                    self.error_occurred.emit(f"Network error or invalid API key: {e}")
                    return
            except Exception as e:
                self.error_occurred.emit(f"Error occurred: {e}")
                return

class APIKeyDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Gemini API Key")
        self.setFixedSize(400, 150)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)

        layout = QVBoxLayout(self)

        self.label_key = QLabel("Enter Gemini API Key")
        self.key_input = QLineEdit()
        self.key_input.setPlaceholderText("Right here")

        self.save_button = QPushButton("Save and Continue")
        self.save_button.clicked.connect(self.accept)

        layout.addWidget(self.label_key)
        layout.addWidget(self.key_input)
        layout.addWidget(self.save_button)

    def get_credentials(self):
        return self.key_input.text().strip()

class AIBrowserApp(QMainWindow):
    def __init__(self, ls_api):
        super().__init__()
        self.setWindowTitle("Daze")
        self.setGeometry(100, 100, 1200, 800)
        self.ls_api = ls_api
        self.last_html_content = ""

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)

        self.top_layout = QHBoxLayout()
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Ask anything")
        self.search_bar.returnPressed.connect(self.start_search)
        self.go_button = QPushButton("Go")
        self.go_button.clicked.connect(self.start_search)
        self.app_drawer_button = QPushButton("Dejigamaflipper")
        self.app_drawer_button.clicked.connect(self.add_to_app_drawer)
        self.app_drawer_button.setEnabled(False)

        self.top_layout.addWidget(self.search_bar)
        self.top_layout.addWidget(self.go_button)
        self.top_layout.addWidget(self.app_drawer_button)
        self.main_layout.addLayout(self.top_layout)

        self.webview = QWebEngineView()
        self.main_layout.addWidget(self.webview)

        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.show_welcome_page()

    def show_welcome_page(self):
        welcome_html = """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>AI Web Browser</title>
            <script src="https://cdn.tailwindcss.com"></script>
            <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;700&display=swap" rel="stylesheet">
            <style>
                body {
                    font-family: 'Inter', sans-serif;
                }
            </style>
        </head>
        <body class="bg-gray-100 p-12 flex items-center justify-center min-h-screen">
            <div class="max-w-2xl bg-white shadow-2xl rounded-3xl p-12 text-center border-4 border-indigo-500">
                <h1 class="text-5xl font-extrabold text-gray-900 mb-4">Welcome to the AI Web Browser</h1>
                <p class="text-xl text-gray-600 mb-8">
                    Enter a query in the search bar above and let AI generate a clean,
                    ad-free HTML page for you.
                </p>
                <div class="mt-8 space-y-4">
                    <p class="text-lg text-gray-500">
                        This application uses the Gemini API to create web content dynamically.
                    </p>
                    <p class="text-sm text-gray-400">
                        Built with Code.
                    </p>
                </div>
            </div>
        </body>
        </html>
        """
        self.webview.setHtml(welcome_html)
        self.app_drawer_button.setEnabled(False)

    def show_loading_page(self):
        loading_html = """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Loading...</title>
            <script src="https://cdn.tailwindcss.com"></script>
            <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;700&display=swap" rel="stylesheet">
            <style>
                body {
                    font-family: 'Inter', sans-serif;
                }
                @keyframes spin {
                    from { transform: rotate(0deg); }
                    to { transform: rotate(360deg); }
                }
                .spinner {
                    animation: spin 1s linear infinite;
                }
            </style>
        </head>
        <body class="bg-gray-100 p-12 flex items-center justify-center min-h-screen">
            <div class="max-w-2xl bg-white shadow-2xl rounded-3xl p-12 text-center border-4 border-indigo-500">
                <div class="flex flex-col items-center">
                    <svg class="spinner w-16 h-16 text-indigo-500" viewBox="0 0 50 50">
                        <circle class="path" cx="25" cy="25" r="20" fill="none" stroke="currentColor" stroke-width="5"></circle>
                    </svg>
                    <p class="mt-4 text-xl font-semibold text-gray-700">Generating your page...</p>
                    <p class="mt-2 text-md text-gray-500">This may take a moment.</p>
                </div>
            </div>
        </body>
        </html>
        """
        self.webview.setHtml(loading_html)
        self.app_drawer_button.setEnabled(False)

    def start_search(self):
        query = self.search_bar.text().strip()
        if not query:
            QMessageBox.warning(self, "Invalid Input", "Please enter something to search.")
            return

        if not self.ls_api:
            QMessageBox.critical(self, "Invalid Configuration", "The API key is incorrect or missing.")
            return
        self.status_bar.showMessage("Generating content...", 0)
        self.show_loading_page()

        self.worker_thread = WorkerThread(query, self.ls_api)
        self.worker_thread.html_generated.connect(self.display_html)
        self.worker_thread.error_occurred.connect(self.display_error)
        self.worker_thread.start()

    def display_html(self, html_content):
        self.webview.setHtml(html_content)
        self.last_html_content = html_content
        self.app_drawer_button.setEnabled(True)
        self.status_bar.showMessage("Content Generated", 5000)

    def display_error(self, error_message):
        QMessageBox.critical(self, "Generation Failed", error_message)
        self.status_bar.showMessage("Error: " + error_message, 5000)
        self.show_welcome_page()

    def add_to_app_drawer(self):
        if not self.last_html_content:
            QMessageBox.warning(self, "Save Error", "No content to save. Generate a page first.")
            return

        query_name = self.search_bar.text().strip().replace(" ", "_").lower()
        file_path = f"generated_pages/{query_name}.html"

        os.makedirs("generated_pages", exist_ok=True)

        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(self.last_html_content)

            QMessageBox.information(self, "Page Saved", f"Page successfully saved to {file_path}")
            self.status_bar.showMessage(f"Page saved: {file_path}", 5000)

        except Exception as e:
            QMessageBox.critical(self, "Save Error", f"Failed to save page: {e}")
            self.status_bar.showMessage(f"Error saving page: {e}", 5000)

if __name__ == "__main__":
    try:
        from PyQt5.QtWebEngineWidgets import QWebEngineView
    except ImportError:
        print("PyQtWebEngine isn't installed.")
        print("Please install it using: pip install PyQtWebEngine")
        sys.exit(1)

    app = QApplication(sys.argv)

    dialog = APIKeyDialog()
    if dialog.exec_():
        ls_api = dialog.get_credentials()
        if not ls_api:
            QMessageBox.critical(None, "API Key Missing", "No API key provided. Exiting.")
            sys.exit(1)

        window = AIBrowserApp(ls_api)
        window.show()
        sys.exit(app.exec_())
    else:
        sys.exit(0)
