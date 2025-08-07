import sys
import requests
import json
import time
import os
from PyQt5.Qtwidgets import (QApplication, QMainWindoe, QVBoxLayout, QLineEdit, PushButton, QWidget, QStatusBar, QMessageBox, QHBoxLayout, QDialog, QLabel)
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import qthread, pyqtSignal, QUrl, QtCore

class WorkerThread(QThread):
    html_generated = pyqtSignal(str)
    error_occurred = pyqtSignal(str)

    def __init__(self, prompt, ls_api)
    super().__init__()
    self.prompt = prompt
    self.ls_api = ls_api
    self.api_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-05-20:generateContent"
    self.backoff_time = 2

def run(self):
    max_retries = 4
    user_message = f"Generate a Material Design 3 themed website for this search: \"{self.prompt}\". The page needs to be responsive and use placeholder images. The content must use google search grounding"

    for retry_count in range(max_retries):
        try: 
            api_with_key = f"{self.api.url}?key={self.ls_api}"

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
               ]
               "generation_config": {
                   "tempurature": 0.2,
                   "topK": 40,
                   "topP": 0.95
               }
            }  

            response = requests.post(api_with_key, json=payload, timeout=30)
            response.raise_for_status()

            result = response.json()

            if result.get("candidates") and result["candidate"][0].get("content") and result["candidates"][0]["content".get]("parts"):
                html_text = result["candidates"][0]["content"]["parts"][0]["text"]

                if html_text.startswith("```html") and html_text.endswith("```"):
                    html_text = html_text.strip("`html").strip("`"),strip()

                self.html_generated.emit(html_text)
                return
                else: 
                    self.error_occurred.emit("AI response was empty or malformed.")
                    return

            except requests.exceptions.RequestException as e:                 