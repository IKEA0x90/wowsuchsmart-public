import os
import tkinter as tk
from tkinter import ttk

# Specify the directory where your audio files are located
audio_directory = "audio/soundpad/"

# Variable to store the selected sound
selected_sound = ""

# Function to update the selected sound when a button is clicked
def update_selected_sound(sound):
    global selected_sound
    selected_sound = sound
    with open("audio/sounds", 'w') as file:
        file.write(selected_sound)

# Function to create buttons for each file in a directory
def create_buttons(directory, frame):
    s = ttk.Style()
    s.configure('.', font=('Arial', 20))

    # Get the list of directories and files in the current directory
    items = os.listdir(directory)

    # Sort the directories alphabetically
    directories = sorted([item for item in items if os.path.isdir(os.path.join(directory, item))])

    # Sort the files alphabetically
    files = sorted([item for item in items if not os.path.isdir(os.path.join(directory, item))])

    # Create buttons for directories first
    for item in directories:
        item_path = os.path.join(directory, item)
        # Create a new frame for the subdirectory
        subframe = ttk.Frame(frame)
        subframe.pack(anchor="w")
        label = ttk.Label(subframe, text=item)
        label.pack(side="left")
        # Recursively create buttons for the subdirectory
        create_buttons(item_path, subframe)

    # Create buttons for files
    for item in files:
        item_path = os.path.join(directory, item)
        # Create a button for the file
        item_name = os.path.splitext(item)[0]
        button = ttk.Button(frame, text=item_name, command=lambda sound=os.path.relpath(item_path, audio_directory): [var.set(sound), update_selected_sound(sound)])
        button.pack(anchor="w")

def on_close():
    with open("audio/sounds", 'w') as file:
        file.write('#STOP')
    root.destroy()

# Create the main window
global window
root = tk.Tk()
root.title("Soundpad GUI")
root.protocol("WM_DELETE_WINDOW", on_close)
# Create a variable to track button clicks
var = tk.StringVar()

# Create a frame for the buttons
button_frame = ttk.Frame(root)
button_frame.pack(side="left", fill="both", expand=True)

# Create a canvas and scrollbar for the button frame
canvas = tk.Canvas(button_frame)
scrollbar = ttk.Scrollbar(button_frame, orient="vertical", command=canvas.yview)
scrollable_frame = ttk.Frame(canvas)

scrollable_frame.bind(
    "<Configure>",
    lambda e: canvas.configure(
        scrollregion=canvas.bbox("all")
    )
)

canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
canvas.configure(yscrollcommand=scrollbar.set)

# Pack the canvas and scrollbar
canvas.pack(side="left", fill="both", expand=True)
scrollbar.pack(side="right", fill="y")

# Set the audio directory path
audio_directory = "audio/soundpad"

# Create buttons for the audio files and directories
create_buttons(audio_directory, scrollable_frame)

# Run the main event loop
root.mainloop()