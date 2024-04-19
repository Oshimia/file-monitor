import os
import time
import shutil
import tkinter as tk
from tkinter import filedialog
import threading

class FileMonitor:
    def __init__(self, file_to_watch, dest_folder):
        self.file_to_watch = file_to_watch
        self.dest_folder = dest_folder
        self.last_modified = self.get_last_modified()

    def get_last_modified(self):
        return os.path.getmtime(self.file_to_watch)

    def monitor_changes(self):
        while True:
            current_modified = self.get_last_modified()
            if current_modified != self.last_modified:
                print("File modified")
                self.duplicate_file()
                self.last_modified = current_modified
            time.sleep(1)

    def duplicate_file(self):
        # Create the destination folder if it doesn't exist
        if not os.path.exists(self.dest_folder):
            os.makedirs(self.dest_folder)

        # Generate the destination file path
        dest_file = os.path.join(self.dest_folder, os.path.basename(self.file_to_watch))

        # Check if the destination file already exists
        counter = 1
        while os.path.exists(dest_file):
            # Append an increasing integer to the file name
            filename, file_extension = os.path.splitext(os.path.basename(self.file_to_watch))
            dest_file = os.path.join(self.dest_folder, f"{filename}_{counter}{file_extension}")
            counter += 1

        # Copy the file
        shutil.copy2(self.file_to_watch, dest_file)
        print(f'File duplicated to: {dest_file}')

def select_file():
    file_to_watch = filedialog.askopenfilename(title="Select File to Watch")
    file_entry.delete(0, tk.END)
    file_entry.insert(0, file_to_watch)

def select_folder():
    dest_folder = filedialog.askdirectory(title="Select Destination Folder")
    folder_entry.delete(0, tk.END)
    folder_entry.insert(0, dest_folder)

def start_monitor():
    file_to_watch = file_entry.get()
    dest_folder = folder_entry.get()

    start_button.config(state=tk.DISABLED)  # Disable the button during monitoring

    monitor = FileMonitor(file_to_watch, dest_folder)
    monitor_thread = threading.Thread(target=monitor.monitor_changes)
    monitor_thread.daemon = True  # Set the thread as daemon to stop it when the main thread exits
    monitor_thread.start()

# Create the main window
root = tk.Tk()
root.title("File Monitor")

# Create and place widgets
file_label = tk.Label(root, text="File to Watch:")
file_label.grid(row=0, column=0, sticky="w")
file_entry = tk.Entry(root, width=50)
file_entry.grid(row=0, column=1, padx=5, pady=5)
file_button = tk.Button(root, text="Browse", command=select_file)
file_button.grid(row=0, column=2, padx=5, pady=5)

folder_label = tk.Label(root, text="Destination Folder:")
folder_label.grid(row=1, column=0, sticky="w")
folder_entry = tk.Entry(root, width=50)
folder_entry.grid(row=1, column=1, padx=5, pady=5)
folder_button = tk.Button(root, text="Browse", command=select_folder)
folder_button.grid(row=1, column=2, padx=5, pady=5)

start_button = tk.Button(root, text="Start Monitoring", command=start_monitor)
start_button.grid(row=2, column=1, pady=10)

# Start the Tkinter event loop
root.mainloop()