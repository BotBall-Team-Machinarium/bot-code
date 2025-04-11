import tkinter as tk
from tkinter import scrolledtext, filedialog
import subprocess
import threading
import queue
import sys
import os
import signal
import time
from datetime import datetime

class ScriptRunner:
    def __init__(self, output_callback, terminal_callback, path_update_callback):
        self.process = None
        self.output_callback = output_callback
        self.terminal_callback = terminal_callback
        self.path_update_callback = path_update_callback
        self.output_queue = queue.Queue()
        self.thread = None
        self.running = False
        self.was_interrupted = False
        self.start_time = None
        self.script_path = os.path.abspath("example_script.py")
        self.path_update_callback(self.script_path)

    def set_script_path(self, path):
        if path:
            self.script_path = os.path.abspath(path)
            self.path_update_callback(self.script_path)

    def start(self):
        if self.running:
            return
        self.running = True
        self.was_interrupted = False
        self.start_time = time.time()
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        start_msg = f">>> [{timestamp}] Running {self.script_path}\n"
        self.output_callback(start_msg, clear=True)
        self.terminal_callback(start_msg)

        def run_script():
            self.process = subprocess.Popen(
                [sys.executable, '-u', self.script_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                bufsize=1,
                text=True,
            )

            for line in self.process.stdout:
                elapsed = time.time() - self.start_time
                formatted_line = f"[{elapsed:.3f}s] {line}"
                self.output_queue.put(formatted_line)

            self.process.wait()
            self.running = False

            end_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            if self.was_interrupted:
                msg = f">>> [{end_time}] Script interrupted.\n"
            else:
                msg = f">>> [{end_time}] Script finished.\n"
            self.output_queue.put(msg)

        self.thread = threading.Thread(target=run_script, daemon=True)
        self.thread.start()
        self._poll_output()

    def _poll_output(self):
        try:
            while True:
                line = self.output_queue.get_nowait()
                self.output_callback(line)
                self.terminal_callback(line)
        except queue.Empty:
            pass

        if self.running or not self.output_queue.empty():
            root.after(100, self._poll_output)

    def stop(self):
        if self.process and self.running:
            self.was_interrupted = True
            if os.name == 'nt':
                self.process.terminate()
            else:
                os.killpg(os.getpgid(self.process.pid), signal.SIGTERM)
            self.running = False

# Tkinter setup
root = tk.Tk()
root.title("Script Runner")
root.attributes('-fullscreen', True)

# Main layout
root.grid_rowconfigure(1, weight=1)  # path bar
root.grid_rowconfigure(2, weight=8)  # terminal + buttons
root.grid_columnconfigure(0, weight=2)  # terminal
root.grid_columnconfigure(1, weight=1)  # buttons

# === Top Control Bar (Close and Minimize) ===
top_bar_frame = tk.Frame(root)
top_bar_frame.grid(row=0, column=0, columnspan=2, sticky="new")
top_bar_frame.grid_columnconfigure(0, weight=1)
top_bar_frame.grid_columnconfigure(1, weight=0)
top_bar_frame.grid_columnconfigure(2, weight=0)

def minimize_window():
    root.iconify()

def close_window():
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    close_msg = f">>> [{timestamp}] Window closed.\n"
    runner.output_callback(close_msg)  # Print the close message
    runner.terminal_callback(close_msg)
    root.quit()

min_btn = tk.Button(top_bar_frame, text="🗕", command=minimize_window)
min_btn.grid(row=0, column=1, sticky="ne", ipadx=10)

close_btn = tk.Button(top_bar_frame, text="✖", command=close_window)
close_btn.grid(row=0, column=2, sticky="ne", ipadx=10)

# === Path Entry Bar ===
script_path_var = tk.StringVar()
script_path_entry = tk.Entry(root, textvariable=script_path_var, state='readonly', font=('Courier', 10))
script_path_entry.grid(row=1, column=0, sticky="nsew", columnspan=2)

# === Terminal Output ===
left_frame = tk.Frame(root)
left_frame.grid(row=2, column=0, sticky="nsew")
left_frame.grid_rowconfigure(0, weight=1)
left_frame.grid_columnconfigure(0, weight=1)

output_field = scrolledtext.ScrolledText(left_frame, wrap=tk.WORD, font=('Courier', 12), state='disabled')
output_field.grid(row=0, column=0, sticky="nsew")

def append_output(text, clear=False):
    output_field.configure(state='normal')
    if clear:
        output_field.delete(1.0, tk.END)
    output_field.insert(tk.END, text)
    output_field.see(tk.END)
    output_field.configure(state='disabled')

def print_terminal(text):
    print(text, end='')

def update_path_display(path):
    script_path_var.set(path)

runner = ScriptRunner(append_output, print_terminal, update_path_display)

# === Right Panel with Buttons ===
btn_frame = tk.Frame(root)
btn_frame.grid(row=2, column=1, sticky="nsew")
btn_frame.grid_rowconfigure(0, weight=2)      # choose button (1/10)
btn_frame.grid_rowconfigure(1, weight=9)    # start button
btn_frame.grid_rowconfigure(2, weight=9)    # stop button
btn_frame.grid_columnconfigure(0, weight=1)

def choose_script():
    path = filedialog.askopenfilename(filetypes=[("Python Scripts", "*.py")])
    if path:
        runner.set_script_path(path)

select_btn = tk.Button(btn_frame, text="Choose Script", command=choose_script)
select_btn.grid(row=0, column=0, sticky="nsew")

start_btn = tk.Button(btn_frame, text="Start Script", command=runner.start)
start_btn.grid(row=1, column=0, sticky="nsew")

stop_btn = tk.Button(btn_frame, text="Stop Script", command=runner.stop)
stop_btn.grid(row=2, column=0, sticky="nsew")

# === Add hover effects to buttons ===
def on_enter(event):
    event.widget.config(bg="#DDDDDD")  # lighter color when hovered

def on_leave(event):
    event.widget.config(bg="#F0F0F0")  # default color when mouse leaves

# Bind hover events to the buttons
for button in [select_btn, start_btn, stop_btn, min_btn, close_btn]:
    button.bind("<Enter>", on_enter)
    button.bind("<Leave>", on_leave)

# Bind close event (when window is closed via X button)
root.protocol("WM_DELETE_WINDOW", close_window)

root.mainloop()
