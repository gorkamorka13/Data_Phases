import tkinter as tk
from tkinter import filedialog, ttk
import pandas as pd
import io

def add_voltagemoy4(data):
    """
    Adds a 'voltagemoy4' column to the given data, calculated as the average of voltagemoy1, voltagemoy2, and voltagemoy3,
    formatted to two decimal places.

    Args:
        data (str): A string containing the data in CSV format.

    Returns:
        str: A string containing the modified data in CSV format, or None if an error occurred.
    """
    try:
        # Read the data into a Pandas DataFrame
        df = pd.read_csv(io.StringIO(data), sep=';')

        # Calculate the average voltage, formatted to two decimal places
        df['voltagemoy4'] = round((df['voltagemoy1'] + df['voltagemoy2'] + df['voltagemoy3']) / 3, 2)

        # Reorder columns to put 'voltagemoy4' in the correct position
        columns = list(df.columns)
        try:
            columns.insert(columns.index('currentmoy4'), columns.pop(columns.index('voltagemoy4')))
        except ValueError as e:
            print(f"Error reordering columns: {e}")
            return None

        df = df[columns]

        # Convert the DataFrame back to a CSV string
        output = df.to_csv(sep=';', index=False)
        return output
    except Exception as e:
        print(f"Error during processing: {e}")
        return None


def browse_file():
    """Opens a file dialog and reads the selected TXT file's content."""
    global original_data  # Access the global variable to store original data
    filename = filedialog.askopenfilename(
        initialdir=".",
        title="Select a Text File",
        filetypes=(("Text files", "*.txt"), ("All files", "*.*")), #Changed here
    )
    if filename:
        try:
            with open(filename, "r") as file:
                original_data = file.read()  # Store in global variable
                update_tables(original_data)  # Update the tables
        except Exception as e:
            original_text.delete("1.0", tk.END) #clear previous content
            modified_text.delete("1.0", tk.END) #clear previous content
            original_text.insert("1.0", f"Error reading file: {e}")
            modified_text.insert("1.0", "Error reading file (see original)")


def update_tables(data):
    """Updates the text in the scrolling frames with original and modified data."""
    global modified_data # to save file

    original_text.delete("1.0", tk.END) # Clear previous content
    modified_text.delete("1.0", tk.END) # Clear previous content

    original_text.insert("1.0", data)

    modified_data = add_voltagemoy4(data)
    if modified_data:
        modified_text.insert("1.0", modified_data)
    else:
        modified_text.insert("1.0", "Error: Could not process data. Check the console for details.")



def save_file():
    """Saves the modified data to a file, removing blank lines."""
    global modified_data
    if not modified_data:
        tk.messagebox.showerror("Error", "No data to save.  Please load and process a file first.")
        return

    filename = filedialog.asksaveasfilename(
        initialdir=".",
        title="Save Modified Data",
        defaultextension=".txt",
        filetypes=(("Text files", "*.txt"), ("All files", "*.*")), # Changed here
    )

    if filename:
        try:
            # Remove extra blank lines before writing
            lines = modified_data.splitlines()
            cleaned_data = "\n".join(line for line in lines if line.strip())  # Remove empty lines

            with open(filename, "w") as file:
                file.write(cleaned_data)
            tk.messagebox.showinfo("Success", "File saved successfully!")
        except Exception as e:
            tk.messagebox.showerror("Error", f"Error saving file: {e}")


# --- Main Tkinter Window Setup ---
root = tk.Tk()
root.title("CSV Processor")

# --- Frames ---
frame_buttons = ttk.Frame(root)
frame_buttons.pack(pady=10)

frame_tables = ttk.Frame(root)
frame_tables.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

# --- Buttons ---
browse_button = ttk.Button(frame_buttons, text="Browse File", command=browse_file)
browse_button.pack(side=tk.LEFT, padx=5)

save_button = ttk.Button(frame_buttons, text="Save Modified File", command=save_file)
save_button.pack(side=tk.LEFT, padx=5)

# --- Scrolling Text Frames ---
# Original Data Frame
original_frame = ttk.Frame(frame_tables)
original_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)

original_label = ttk.Label(original_frame, text="Original Data:")
original_label.pack()

original_text = tk.Text(original_frame, wrap=tk.NONE)
original_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

original_scrollbar_x = ttk.Scrollbar(original_frame, orient=tk.HORIZONTAL, command=original_text.xview)
original_scrollbar_x.pack(side=tk.BOTTOM, fill=tk.X)
original_text.configure(xscrollcommand=original_scrollbar_x.set)

original_scrollbar_y = ttk.Scrollbar(original_frame, orient=tk.VERTICAL, command=original_text.yview)
original_scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)
original_text.configure(yscrollcommand=original_scrollbar_y.set)

# Modified Data Frame
modified_frame = ttk.Frame(frame_tables)
modified_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)

modified_label = ttk.Label(modified_frame, text="Modified Data:")
modified_label.pack()

modified_text = tk.Text(modified_frame, wrap=tk.NONE)
modified_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

modified_scrollbar_x = ttk.Scrollbar(modified_frame, orient=tk.HORIZONTAL, command=modified_text.xview)
modified_scrollbar_x.pack(side=tk.BOTTOM, fill=tk.X)
modified_text.configure(xscrollcommand=modified_scrollbar_x.set)

modified_scrollbar_y = ttk.Scrollbar(modified_frame, orient=tk.VERTICAL, command=modified_text.yview)
modified_scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)
modified_text.configure(yscrollcommand=modified_text.yview)

# --- Global Variables ---
original_data = ""  # Stores data from selected file
modified_data = "" # Store modified data so it can be saved

root.mainloop()