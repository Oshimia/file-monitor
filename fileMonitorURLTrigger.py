import os
import time
import tkinter as tk
from tkinter import filedialog
import threading
import requests

class FileMonitor:
    def __init__(self, file_to_watch, target_url):
        self.file_to_watch = file_to_watch
        self.target_url = target_url
        if not os.path.exists(self.file_to_watch):
            raise FileNotFoundError(f"File not found: {self.file_to_watch}")
        self.last_modified = self.get_last_modified()

    def get_last_modified(self):
        return os.path.getmtime(self.file_to_watch)

    def monitor_changes(self):
        while True:
            try:
                current_modified = self.get_last_modified()
                if current_modified != self.last_modified:
                    print("File modified")
                    self.trigger_http_request()
                    self.last_modified = current_modified
            except FileNotFoundError:
                print(f"Error: Monitored file '{self.file_to_watch}' not found. Stopping monitor.")
                # Re-enable start button if GUI is accessible from here, or use a callback
                # For simplicity, we'll just break the loop.
                # If you want to re-enable the button, you'd need to pass a reference or use a more complex event system.
                if 'start_button' in globals() and start_button: # Check if start_button is accessible
                     start_button.config(state=tk.NORMAL)
                break
            except Exception as e:
                print(f"An error occurred during monitoring: {e}")
            time.sleep(1)

    def trigger_http_request(self):
        try:
            # Changed from requests.get to requests.post
            # No data payload is being sent in this example, but POST allows it.
            response = requests.post(self.target_url)
            response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx)
            print(f"Successfully triggered URL via POST: {self.target_url}, Status: {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"Error triggering URL {self.target_url} via POST: {e}")

def select_file():
    file_to_watch = filedialog.askopenfilename(title="Select File to Watch")
    if file_to_watch:
        file_entry.delete(0, tk.END)
        file_entry.insert(0, file_to_watch)

def start_monitor():
    global monitor_thread_active # To manage thread state
    file_to_watch = file_entry.get()
    target_url = url_entry.get()

    if not file_to_watch:
        tk.messagebox.showerror("Error", "Please select a file to watch.")
        return

    if not target_url:
        tk.messagebox.showerror("Error", "Please enter a target URL.")
        return

    if not (target_url.startswith('http://') or target_url.startswith('https://')):
        tk.messagebox.showerror("Error", "Target URL must start with http:// or https://")
        return

    try:
        monitor = FileMonitor(file_to_watch, target_url)
    except FileNotFoundError as e:
        tk.messagebox.showerror("Error", str(e))
        return
    except Exception as e:
        tk.messagebox.showerror("Error", f"Error initializing monitor: {e}")
        return

    start_button.config(state=tk.DISABLED)
    stop_button.config(state=tk.NORMAL) # Enable stop button

    # Use a shared event to signal the thread to stop
    global stop_monitoring_event
    stop_monitoring_event = threading.Event()

    # Modify FileMonitor to accept and check the event
    monitor.stop_event = stop_monitoring_event
    # Modify monitor_changes to check stop_event
    original_monitor_changes = monitor.monitor_changes
    def new_monitor_changes():
        while not stop_monitoring_event.is_set():
            try:
                current_modified = monitor.get_last_modified()
                if current_modified != monitor.last_modified:
                    print("File modified")
                    monitor.trigger_http_request()
                    monitor.last_modified = current_modified
            except FileNotFoundError:
                print(f"Error: Monitored file '{monitor.file_to_watch}' not found. Stopping monitor.")
                if 'root' in globals() and root.winfo_exists(): # Check if GUI exists
                    root.after(0, lambda: stop_button.config(state=tk.DISABLED))
                    root.after(0, lambda: start_button.config(state=tk.NORMAL))
                break
            except Exception as e:
                print(f"An error occurred during monitoring: {e}")
            # Check event more frequently than just time.sleep(1)
            if stop_monitoring_event.wait(1): # Wait for 1 sec or until event is set
                break
        print("Monitoring stopped.")
        if 'root' in globals() and root.winfo_exists():
             root.after(0, lambda: start_button.config(state=tk.NORMAL)) # Re-enable start button
             root.after(0, lambda: stop_button.config(state=tk.DISABLED)) # Disable stop button


    monitor_thread = threading.Thread(target=new_monitor_changes)
    monitor_thread.daemon = True
    monitor_thread.start()
    monitor_thread_active = True
    print(f"Monitoring '{os.path.basename(file_to_watch)}'. Triggering URL '{target_url}' on modification.")

def stop_monitor():
    global stop_monitoring_event
    if stop_monitoring_event:
        print("Stop signal sent to monitoring thread.")
        stop_monitoring_event.set()
    stop_button.config(state=tk.DISABLED)
    # Start button will be re-enabled by the thread itself when it exits


# --- Main GUI Setup ---
root = tk.Tk()
root.title("File Monitor & URL Trigger")

# Global variable to hold the stop event for the monitoring thread
stop_monitoring_event = None
monitor_thread_active = False # Flag to track if monitoring is active

# File selection
file_label = tk.Label(root, text="File to Watch:")
file_label.grid(row=0, column=0, sticky="w", padx=(10,0), pady=5)
file_entry = tk.Entry(root, width=50)
file_entry.grid(row=0, column=1, padx=5, pady=5)
file_button = tk.Button(root, text="Browse...", command=select_file)
file_button.grid(row=0, column=2, padx=5, pady=5)

# URL input
url_label = tk.Label(root, text="Target URL (POST):")
url_label.grid(row=1, column=0, sticky="w", padx=(10,0), pady=5)
url_entry = tk.Entry(root, width=50)
url_entry.grid(row=1, column=1, padx=5, pady=5)
# Example URL for testing
url_entry.insert(0, "https://httpbin.org/post")


# Control buttons
button_frame = tk.Frame(root)
button_frame.grid(row=2, column=0, columnspan=3, pady=10)

start_button = tk.Button(button_frame, text="Start Monitoring", command=start_monitor, width=15)
start_button.pack(side=tk.LEFT, padx=5)

stop_button = tk.Button(button_frame, text="Stop Monitoring", command=stop_monitor, state=tk.DISABLED, width=15)
stop_button.pack(side=tk.LEFT, padx=5)

# Ensure thread is stopped gracefully on window close
def on_closing():
    if stop_monitoring_event:
        stop_monitoring_event.set()
    # Give the thread a moment to shut down
    # For a more robust solution, you might join the thread here with a timeout
    # but daemon=True should handle most cases if the main Tk loop ends cleanly.
    root.destroy()

root.protocol("WM_DELETE_WINDOW", on_closing)
root.mainloop()
