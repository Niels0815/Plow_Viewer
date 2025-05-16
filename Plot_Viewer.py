import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('TkAgg')

import tkinter as tk
from tkinter import filedialog, messagebox
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class CSVPlotApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Flexible Multi-Plot CSV Viewer")

        self.df = None
        self.current_file = None
        self.autoupdate = False
        self.refresh_interval_ms = 1000
        self.checkbox_vars = {}
        self.diagram_assignments = {}
        self.y_axis_modes = {}
        self.num_diagrams = tk.IntVar(value=1)

        # GUI Layout
        self.load_button = tk.Button(root, text="Select CSV File", command=self.load_csv)
        self.load_button.pack(pady=5)

        self.file_label = tk.Label(root, text="No file loaded.")
        self.file_label.pack()

        # Diagram count selection
        tk.Label(root, text="Number of Diagrams:").pack()
        self.diagram_selector = tk.Spinbox(root, from_=1, to=5, textvariable=self.num_diagrams, command=self.generate_checkboxes)
        self.diagram_selector.pack(pady=5)

        # Full diagram checkbox
        self.full_diagram_var = tk.BooleanVar(value=True)
        self.full_diagram_check = tk.Checkbutton(root, text="Use full dataset (disable time window & slider)", variable=self.full_diagram_var, command=self.toggle_time_controls)
        self.full_diagram_check.pack()

        # Time window controls
        self.time_controls_frame = tk.Frame(root)
        # Initially hide time controls if full dataset is selected
        if not self.full_diagram_var.get():
            self.time_controls_frame.pack()

        tk.Label(self.time_controls_frame, text="Time Window:").pack()
        self.time_window_entry = tk.Entry(self.time_controls_frame, width=10)
        self.time_window_entry.insert(0, "5")
        self.time_window_entry.pack()

        self.unit_var = tk.StringVar()
        self.unit_var.set("minutes")
        unit_menu = tk.OptionMenu(self.time_controls_frame, self.unit_var, "seconds", "minutes", "hours")
        unit_menu.pack()

        tk.Label(self.time_controls_frame, text="Scroll Time Offset:").pack()
        self.offset_slider = tk.Scale(self.time_controls_frame, from_=0, to=100, orient='horizontal', length=300)
        self.offset_slider.pack()
        self.offset_slider.bind("<ButtonRelease-1>", lambda event: self.update_plot())

        # Checkboxes and Y-axis control per diagram
        self.checkbox_frame = tk.Frame(root)
        self.checkbox_frame.pack(pady=10, fill=tk.X)

        self.plot_button = tk.Button(root, text="Plot Selected", command=self.update_plot)
        self.plot_button.pack(pady=5)

        self.auto_button = tk.Button(root, text="Start Auto-Update", command=self.toggle_auto_update)
        self.auto_button.pack(pady=5)

        self.fig, self.axes = plt.subplots(1, 1, figsize=(10, 4))
        self.canvas = FigureCanvasTkAgg(self.fig, master=root)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def toggle_time_controls(self):
        if self.full_diagram_var.get():
            self.time_controls_frame.pack_forget()
        else:
            self.time_controls_frame.pack()

    def load_csv(self):
        file_path = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
        if not file_path:
            return

        try:
            self.df = pd.read_csv(file_path, delimiter=';')
            self.df.columns = [col.strip() for col in self.df.columns]
            timestamp_col = next((col for col in self.df.columns if "time" in col.lower()), self.df.columns[1])
            self.df['timestamp'] = pd.to_datetime(self.df[timestamp_col], errors='coerce')
            self.current_file = file_path

            self.file_label.config(text=f"Loaded: {file_path.split('/')[-1]}")
            self.offset_slider.config(to=max(0, len(self.df) - 1))
            self.generate_checkboxes()
            self.update_plot()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load file:\n{e}")

    def generate_checkboxes(self):
        for widget in self.checkbox_frame.winfo_children():
            widget.destroy()
        self.checkbox_vars.clear()
        self.diagram_assignments.clear()
        self.y_axis_modes.clear()

        num = self.num_diagrams.get()
        for i in range(num):
            frame = tk.LabelFrame(self.checkbox_frame, text=f"Diagram {i+1}")
            frame.pack(side=tk.LEFT, fill=tk.Y, padx=10)
            self.diagram_assignments[i] = []

            # Column selection checkboxes
            for col in self.df.columns:
                if col == 'timestamp':
                    continue
                var = tk.BooleanVar()
                cb = tk.Checkbutton(frame, text=col, variable=var, command=self.update_plot)
                cb.pack(anchor='w')
                self.checkbox_vars[(i, col)] = var

            # Y-axis scale selector
            mode_var = tk.StringVar()
            mode_var.set("auto")
            self.y_axis_modes[i] = mode_var
            tk.Label(frame, text="Y-Axis Scale:").pack()
            tk.OptionMenu(frame, mode_var, "auto", "custom").pack()

            min_entry = tk.Entry(frame, width=8)
            min_entry.insert(0, "0")
            max_entry = tk.Entry(frame, width=8)
            max_entry.insert(0, "100")
            min_entry.pack()
            max_entry.pack()
            self.y_axis_modes[f"min_{i}"] = min_entry
            self.y_axis_modes[f"max_{i}"] = max_entry

    def update_plot(self):
        if self.df is None or self.df.empty:
            return

        try:
            if self.full_diagram_var.get():
                filtered_df = self.df.copy()
            else:
                window_val = int(self.time_window_entry.get().strip())
                unit = self.unit_var.get()
                delta = pd.to_timedelta(window_val, unit=unit)

                offset_index = int(self.offset_slider.get())
                if offset_index >= len(self.df):
                    offset_index = len(self.df) - 1

                offset_time = self.df['timestamp'].iloc[offset_index]
                start_time = offset_time
                end_time = offset_time + delta

                filtered_df = self.df[(self.df['timestamp'] >= start_time) & (self.df['timestamp'] <= end_time)]

            num = self.num_diagrams.get()
            self.fig.clf()
            self.axes = self.fig.subplots(num, 1, sharex=True)
            if num == 1:
                self.axes = [self.axes]

            for i, ax in enumerate(self.axes):
                ax.clear()
                assigned_cols = [col for (d, col), var in self.checkbox_vars.items() if d == i and var.get()]
                for col in assigned_cols:
                    ax.plot(filtered_df['timestamp'], filtered_df[col], label=col)

                ax.set_ylabel("Value")
                ax.set_title(f"Diagram {i+1}")
                ax.grid(True)
                ax.legend()

                if self.y_axis_modes[i].get() == "custom":
                    try:
                        ymin = float(self.y_axis_modes[f"min_{i}"].get())
                        ymax = float(self.y_axis_modes[f"max_{i}"].get())
                        ax.set_ylim(ymin, ymax)
                    except ValueError:
                        pass

            self.axes[-1].set_xlabel("Time")
            self.fig.autofmt_xdate()
            self.canvas.draw()

        except Exception as e:
            print(f"Plot update error: {e}")

    def toggle_auto_update(self):
        self.autoupdate = not self.autoupdate
        self.auto_button.config(text="Stop Auto-Update" if self.autoupdate else "Start Auto-Update")
        if self.autoupdate:
            self.schedule_update()

    def schedule_update(self):
        if not self.autoupdate or not self.current_file:
            return
        try:
            self.df = pd.read_csv(self.current_file, delimiter=';')
            self.df.columns = [col.strip() for col in self.df.columns]
            timestamp_col = next((col for col in self.df.columns if "time" in col.lower()), self.df.columns[1])
            self.df['timestamp'] = pd.to_datetime(self.df[timestamp_col], errors='coerce')
            self.offset_slider.config(to=max(0, len(self.df) - 1))
            self.update_plot()
        except Exception as e:
            print(f"Auto-update failed: {e}")
        finally:
            self.root.after(self.refresh_interval_ms, self.schedule_update)

# Run the app
if __name__ == "__main__":
    root = tk.Tk()
    app = CSVPlotApp(root)
    root.mainloop()



