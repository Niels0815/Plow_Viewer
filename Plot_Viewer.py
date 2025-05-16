import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('TkAgg')
import tkinter as tk
from tkinter import filedialog, messagebox

class CSVPlotApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Dynamic CSV Plot Viewer")
        self.df = None
        self.checkbox_vars = {}
        self.checkboxes = []

        self.load_button = tk.Button(root, text="Select CSV File", command=self.load_csv)
        self.load_button.pack(pady=5)

        self.file_label = tk.Label(root, text="No file loaded.")
        self.file_label.pack()

        self.checkbox_frame = tk.Frame(root)
        self.checkbox_frame.pack(pady=10)

        # Add time range entry fields
        tk.Label(root, text="Start Time (e.g. 2025-05-14 11:30:00)").pack()
        self.start_time_entry = tk.Entry(root, width=30)
        self.start_time_entry.pack()

        tk.Label(root, text="End Time (e.g. 2025-05-14 12:30:00)").pack()
        self.end_time_entry = tk.Entry(root, width=30)
        self.end_time_entry.pack()

        self.plot_button = tk.Button(root, text="Plot Selected", command=self.plot_selected)
        self.plot_button.pack(pady=10)


    def load_csv(self):
        file_path = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
        if not file_path:
            return

        try:
            # Read with semicolon delimiter
            self.df = pd.read_csv(file_path, delimiter=';')
            self.df.columns = [col.strip() for col in self.df.columns]

            # Find timestamp-like column
            timestamp_col = next((col for col in self.df.columns if "time" in col.lower()), self.df.columns[1])
            self.df['timestamp'] = pd.to_datetime(self.df[timestamp_col], errors='coerce')

            self.file_label.config(text=f"Loaded: {file_path.split('/')[-1]}")
            self.generate_checkboxes()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load file:\n{e}")

    def generate_checkboxes(self):
        # Clear old checkboxes
        for widget in self.checkbox_frame.winfo_children():
            widget.destroy()
        self.checkbox_vars.clear()

        for col in self.df.columns:
            if col == 'timestamp':
                continue  # Don't plot timestamp itself
            var = tk.BooleanVar()
            cb = tk.Checkbutton(self.checkbox_frame, text=col, variable=var)
            cb.pack(anchor='w')
            self.checkbox_vars[col] = var
            
    def plot_selected(self):
        if self.df is None:
            messagebox.showwarning("No File", "Please load a CSV file first.")
            return

        # Get time range from user input
        start_str = self.start_time_entry.get().strip()
        end_str = self.end_time_entry.get().strip()

        try:
            start_time = pd.to_datetime(start_str) if start_str else self.df['timestamp'].min()
            end_time = pd.to_datetime(end_str) if end_str else self.df['timestamp'].max()
        except Exception as e:
            messagebox.showerror("Time Format Error", f"Could not parse time input:\n{e}")
            return

        # Filter the DataFrame
        filtered_df = self.df[(self.df['timestamp'] >= start_time) & (self.df['timestamp'] <= end_time)]

        selected_cols = [col for col, var in self.checkbox_vars.items() if var.get()]
        if not selected_cols:
            messagebox.showinfo("No Selection", "Please select at least one column to plot.")
            return

        plt.figure(figsize=(14, 6))
        for col in selected_cols:
            plt.plot(filtered_df['timestamp'], filtered_df[col], label=col)

        plt.xlabel("Time")
        plt.ylabel("Value")
        plt.title(f"Selected Columns from {start_time} to {end_time}")
        plt.legend()
        plt.grid(True)
        plt.tight_layout()
        plt.xticks(rotation=45)
        plt.show()

# Run the app
if __name__ == "__main__":
    root = tk.Tk()
    app = CSVPlotApp(root)
    root.mainloop()
