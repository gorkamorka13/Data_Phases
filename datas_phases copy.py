# *******************************************
# Visualisation des données de phases
# Michel ESPARSA - Version 2.1 du 01/03/2025
# - Création de checkbox pour choisir le type de fenetres à afficher
# - Intégration du bitmap logo au fichier source
# - Ajout de la fonctionalité "phase4"
# - Ajout des Min et Max (dates)aux fenetres Comparaison
# - Ajout des Min et Max (dates) aux fenetre de phases
# - Ajout de la moyenne glissante
# - Ajout d'un marqueur aux max pour les fenetres de Comparaison
# - Ajout du jour aux axes des abscisses
# Michel ESPARSA - Version 2.2 du 08/03/2025
# - Inversion des value sliders
# - Ajout de la fonctionnalité de calendrier
#********************************************

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
import matplotlib.dates as mdates
from datetime import datetime
from PIL import Image, ImageTk
import numpy as np
import os,sys
import resources
import io
import base64

import tkinter as tk
from tkinter import ttk
import calendar
from datetime import datetime, date
from datetime import datetime, time

class Calendar(tk.Toplevel):
    def __init__(self, parent, min_date, max_date):
        super().__init__(parent)
        self.title("Select Date")
        self.geometry("300x250")  # Adjust as needed
        self.resizable(False, False)
        self.transient(parent) # Make it a modal dialog

        self.min_date = min_date
        self.max_date = max_date
        self.selected_date = None # Initialize

        self.cal = calendar.Calendar()
        self.year = self.min_date.year
        self.month = self.min_date.month

        self.month_label = ttk.Label(self, text="", font=("Arial", 12, "bold"))
        self.month_label.pack(pady=5)

        self.calendar_frame = ttk.Frame(self)
        self.calendar_frame.pack(pady=5)

        self.prev_button = ttk.Button(self, text="<", command=self.prev_month)
        self.next_button = ttk.Button(self, text=">", command=self.next_month)

        self.prev_button.pack(side=tk.LEFT, padx=5)
        self.next_button.pack(side=tk.RIGHT, padx=5)

        self.draw_calendar()

        self.protocol("WM_DELETE_WINDOW", self.close_window) # Handle close button

        self.wait_window(self)  # Keep the window open until it's closed
        
    def draw_calendar(self):
        for widget in self.calendar_frame.winfo_children():
            widget.destroy()

        self.month_label.config(text=f"{calendar.month_name[self.month]} {self.year}")

        days = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
        for col, day in enumerate(days):
            ttk.Label(self.calendar_frame, text=day, width=3, anchor="center").grid(row=0, column=col, padx=1, pady=1)

        month_days = self.cal.monthdayscalendar(self.year, self.month)

        for row, week in enumerate(month_days):
            for col, day in enumerate(week):
                if day != 0:
                    current_date = date(self.year, self.month, day)
                    if self.min_date.date() <= current_date <= self.max_date.date():
                        button = ttk.Button(self.calendar_frame, text=day, width=3, command=lambda d=day: self.select_date(d))
                        button.grid(row=row + 1, column=col, padx=1, pady=1)
                    else:
                        label = ttk.Label(self.calendar_frame, text=day, width=3, anchor="center", foreground="gray")
                        label.grid(row=row + 1, column=col, padx=1, pady=1)

    def prev_month(self):
        self.month -= 1
        if self.month < 1:
            self.month = 12
            self.year -= 1
        if date(self.year, self.month, 1) < self.min_date.date():
            self.year = self.min_date.year
            self.month = self.min_date.month
        self.draw_calendar()

    def next_month(self):
        self.month += 1
        if self.month > 12:
            self.month = 1
            self.year += 1
        if date(self.year, self.month, calendar.monthrange(self.year, self.month)[1]) > self.max_date.date():
            self.year = self.max_date.year
            self.month = self.max_date.month
        self.draw_calendar()

    def select_date(self, day):
        self.selected_date = date(self.year, self.month, day)      
        self.close_window() # Close when date is selected
        
    def close_window(self):
        self.destroy() # Destroy the window

class ComparisonWindow:                       
    @staticmethod
    def lissage(signal_brut,L):
        res = np.copy(signal_brut) # duplication des valeurs
        for i in range (1,len(signal_brut)-1): # toutes les valeurs sauf la première et la dernière
            L_g = min(i,L) # nombre de valeurs disponibles à gauche
            L_d = min(len(signal_brut)-i-1,L) # nombre de valeurs disponibles à droite
            Li=min(L_g,L_d)
            res[i]=np.sum(signal_brut[i-Li:i+Li+1])/(2*Li+1)
        return res
        
    def resources_path(self,relative_path):
        try:
            base_path=sys.MEIPASS
        except Exception:
            base_path=os.path.abspath(".")
        return os.path.join(base_path,relative_path)    

    def open_calendar(self):        
        cal = Calendar(self.window, self.min_time, self.max_time)  # Pass min/max dates
        self.selected_calendar_date = cal.selected_date # Retrieve selected date
        if self.selected_calendar_date:
            # self.min_time = self.data['time'].min()
            # self.max_time = self.data['time'].max()        
            # print(f"\n0) self.min_time: {self.min_time}")       
            # print(f"0) self.max_time: {self.max_time}")
            position_slider_start=self.start_slider.get()  
            position_slider_end=self.end_slider.get()  
            old_start_date= self.min_time + pd.Timedelta(seconds=int(position_slider_start))
            # print(f"old_start_date: {old_start_date}")
            old_end_date= self.min_time + pd.Timedelta(seconds=int(position_slider_end))
            # print(f"old_end_date: {old_end_date}")

            # print(f"Selected date: {self.selected_calendar_date}")
            date_object = datetime.combine(self.selected_calendar_date, time(0, 0, 0))                     
            new_start_date = date_object + pd.Timedelta(seconds=int(0))
                       
            # si la date selectionnée calendrier est inférieure à la date de début des données
            if (new_start_date-self.min_time).total_seconds() < 0:
                new_start_date = self.min_time
            # print(f"1)new_start_date: {new_start_date}")
                            
            # nombre de secondes entre le début des données et la date selectionnée dans le calendrier
            diff_begin_seconds = int((new_start_date-self.min_time).total_seconds())
            # print(f"2)diff_begin_seconds: {diff_begin_seconds}")
                          
            # date selectionnée dans le calendrier plus 24 heures en secondes
            new_end_date = date_object + pd.Timedelta(seconds=int(24*3600-1))
            diff_end_seconds = int((new_end_date - new_start_date).total_seconds()) 
            # print(f"3)new_end_date: {new_end_date}")            
            
            # si la date selectionnée calendrier est supérieure à la date de fin des données alors on deplace slider end d'abord (et inversement)
            if (new_start_date - old_start_date).total_seconds() < 0:         
                self.start_slider.set(diff_begin_seconds) 
                self.end_slider.set(diff_begin_seconds + diff_end_seconds)
            else:
                self.end_slider.set(diff_begin_seconds + diff_end_seconds)
                self.start_slider.set(diff_begin_seconds)                 
                                         
                    
    def __init__(self, parent, data, plot_type):
        
        # Inside ComparisonWindow's __init__:
        self.selected_calendar_date = None
        # Create window
        self.window = tk.Toplevel(parent)
        self.window.title(f"{plot_type} Comparison - All Phases")
        self.window.geometry("1200x800")  # Increased width for sliders

        # First decode the base64 string into binary data
        decoded_data = base64.b64decode(resources.bolt64x64)
        # Then create an image from the binary data
        self.image = Image.open(io.BytesIO(decoded_data))
        # Convert PIL image to Tkinter PhotoImage
        photo = ImageTk.PhotoImage(self.image)
        # Set the window icon
        self.window.iconphoto(False, photo)
        # Keep a reference to prevent garbage collection
        self.photo = photo

        # Store data and type
        self.data = data.copy()  # Make a copy to prevent modifications to original data
        self.filtered_data = self.data.copy()
        self.plot_type = plot_type
        
        # Checkbox for adding all phases data (only for Current and Power windows)
        if self.plot_type in ["Current", "Power"]:
            self.all_phases_var = tk.BooleanVar(value=False)  
            self.all_phases_var.trace_add('write', lambda *args: self.on_phase_toggle())                  

        try:
            # Convert time column           
            self.data['time'] = pd.to_datetime(self.data['time'], format='%d/%m/%Y %H:%M:%S')

            # Get time range
            self.min_time = self.data['time'].min()
            self.max_time = self.data['time'].max()
            self.total_seconds = int((self.max_time - self.min_time).total_seconds())

            # Calculate global value across all phases
            self.global_min = self.data[self.get_column_names()].min().min()
            self.global_max = self.data[self.get_column_names()].max().max()

            # Initialize GUI components
            self.initialize_gui()

        except Exception as e:
            messagebox.showerror("Initialization Error", f"Error during initialization: {str(e)}")
            self.window.destroy()
            raise

    def initialize_gui(self):
        """Initialize all GUI components in the correct order"""
        # Main container
        self.main_frame = ttk.Frame(self.window)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Create frames for different sections
        self.controls_frame = ttk.Frame(self.main_frame)
        self.controls_frame.pack(fill=tk.X, side=tk.TOP)

        self.plot_frame = ttk.Frame(self.main_frame)
        self.plot_frame.pack(fill=tk.BOTH, expand=True, side=tk.LEFT)

        self.slider_frame = ttk.Frame(self.main_frame, width=100)
        self.slider_frame.pack(fill=tk.Y, side=tk.RIGHT, padx=10)

        # Phase checkboxes
        self.phase_checkboxes_frame = ttk.Frame(self.controls_frame)
        self.phase_checkboxes_frame.pack(fill=tk.X, padx=5, pady=5)

        # Initialize components in order   
        self.create_plot()
        self.create_time_controls()
        self.create_value_sliders()      
        self.min_slider.set(self.global_min)               
        self.end_slider.set(self.total_seconds)

    def create_plot(self):
        """Create the matplotlib plot area"""
        try:
            self.fig = Figure(figsize=(10, 8))
            self.ax = self.fig.add_subplot(111)

            self.canvas = FigureCanvasTkAgg(self.fig, self.plot_frame)
            self.canvas.draw()
            self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        except Exception as e:
            messagebox.showerror("Plot Error", f"Error creating plot: {str(e)}")
            raise

    def create_time_controls(self):
        """Create time control widgets"""
        # ******************************Time range frame
        time_frame = ttk.LabelFrame(self.controls_frame, text="Time Range Selection", padding="5")
        time_frame.pack(fill=tk.X, padx=5, pady=5)

        # Entry frame
        entry_frame = ttk.Frame(time_frame)
        entry_frame.pack(fill=tk.X, pady=5)
        
        # Start time
        ttk.Label(entry_frame, text="Start:").pack(side=tk.LEFT, padx=5)
        self.start_var = tk.StringVar(value=self.min_time.strftime('%Y-%m-%d %H:%M:%S'))
        ttk.Entry(entry_frame, textvariable=self.start_var, width=20).pack(side=tk.LEFT, padx=5)

        # End time
        ttk.Label(entry_frame, text="End:").pack(side=tk.LEFT, padx=5)
        self.end_var = tk.StringVar(value=self.max_time.strftime('%Y-%m-%d %H:%M:%S'))
        ttk.Entry(entry_frame, textvariable=self.end_var, width=20).pack(side=tk.LEFT, padx=5)

        # Points counter
        self.points_var = tk.StringVar(value="Points: 0")
        ttk.Label(entry_frame, textvariable=self.points_var, font=('Arial', 10, 'bold')).pack(side=tk.LEFT, padx=15)

        # Time elapsed label
        self.time_elapsed_var = tk.StringVar(value="Time Elapsed: 0s")
        ttk.Label(entry_frame, textvariable=self.time_elapsed_var, font=('Arial', 10, 'bold')).pack(side=tk.LEFT, padx=15)
        
        # Button
        ttk.Button(entry_frame, text="Reset", command=self.reset_range).pack(side=tk.LEFT, padx=5)
        
                # Inside ComparisonWindow's create_time_controls:
        ttk.Button(entry_frame, text="Calendar", command=self.open_calendar).pack(side=tk.LEFT, padx=5)

        # Sliders
        self.create_time_sliders(time_frame)
        
        # Checkboxes
        self.create_checkboxes(time_frame)        
        
    def create_checkboxes(self, parent):
        # *******************************Checkboxes Frame in time_frame-> visibility_frame
        visibility_frame = ttk.Frame(parent)
        visibility_frame.pack(fill=tk.X, pady=5)
        ttk.Label(visibility_frame, text="Visible Phases:", font=('Arial', 10)).pack(side=tk.LEFT, padx=5)
        
        # Liste des phases checkboxes
        self.phase_visibility = {
            'Phase 1': tk.BooleanVar(value=True),
            'Phase 2': tk.BooleanVar(value=True),
            'Phase 3': tk.BooleanVar(value=True),
            'Phase 4': tk.BooleanVar(value=True)
        }

        # Création des phases checkboxes
        colors = ['blue', 'red', 'green','grey']
        for i, (phase, var) in enumerate(self.phase_visibility.items()):
            cb = ttk.Checkbutton(
                visibility_frame, 
                text=phase,
                variable=var,
                command=lambda: self.on_phase_toggle(),
                style=f'Color{i+1}.TCheckbutton'
            )
            cb.pack(side=tk.LEFT, padx=10)
            
            # Create colored label next to checkbox
            color_label = ttk.Label(visibility_frame, text="■", foreground=colors[i])
            color_label.pack(side=tk.LEFT, padx=(0, 10))
        
        # Création de lacheckbox pour tracer la moyenne glissante
        self.mean_var = tk.BooleanVar(value=False)                  
        cb = ttk.Checkbutton(
            visibility_frame, 
            text="Moyenne",
            variable=self.mean_var,
            command=lambda: self.on_phase_toggle(),
            style='purple.TCheckbutton'
        )
        cb.pack(side=tk.LEFT, padx=10)        
        # Create colored label next to checkbox
        color_label = ttk.Label(visibility_frame, text="■", foreground="purple")
        color_label.pack(side=tk.LEFT, padx=(0, 5))  
        
        self.input_field = ttk.Entry(visibility_frame,width=4,textvariable="n")
        self.input_field.pack(side=tk.LEFT, padx=1)
        self.input_field.setvar("n","10")
        self.input_field.bind("<Return>", lambda event: self.on_phase_toggle())        
                                           
        #Début de création des labels de données (energie, max, min)
        if self.plot_type=="Power":
            self.energy_var = tk.StringVar(value="Energy: -- kWh")
            ttk.Label(visibility_frame, textvariable=self.energy_var, font=('Arial', 10, 'bold')).pack(side=tk.LEFT, padx=5)
            
        # Max value
        self.max_value_var = tk.StringVar(value="Max: ")
        ttk.Label(visibility_frame, textvariable= self.max_value_var, font=('Arial', 10, 'bold')).pack(side=tk.LEFT, padx=15)
        
        # Min value
        self.min_value_var = tk.StringVar(value="Min: ")
        ttk.Label(visibility_frame, textvariable= self.min_value_var, font=('Arial', 10, 'bold')).pack(side=tk.LEFT, padx=15)
                
    def create_time_sliders(self, parent):  
        """Create the time range sliders"""
        # Start slider
        start_frame = ttk.Frame(parent)
        start_frame.pack(fill=tk.X, pady=2)
        ttk.Label(start_frame, text="Start Time:").pack(side=tk.LEFT, padx=5)
        self.start_slider = ttk.Scale(
            start_frame, from_=0, to=self.total_seconds,
            orient=tk.HORIZONTAL, command=self.on_start_slide
        )
        self.start_slider.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        # End slider
        end_frame = ttk.Frame(parent)
        end_frame.pack(fill=tk.X, pady=2)
        ttk.Label(end_frame, text="End Time:").pack(side=tk.LEFT, padx=5)
        self.end_slider = ttk.Scale(
            end_frame, from_=0, to=self.total_seconds,
            orient=tk.HORIZONTAL, command=self.on_end_slide
        )
        self.end_slider.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

    def create_value_sliders(self):
        """Create vertical sliders for filtering data by column values"""
        self.max_label = ttk.Label(self.slider_frame, text=f"Max value: {self.global_max}", font=("Arial", 10, "bold"))
        self.max_label.pack(pady=5)

        self.max_slider = ttk.Scale(
            self.slider_frame, from_=self.global_max, 
            to=self.global_min,
            orient=tk.VERTICAL, command=self.on_max_slide
        )
        self.max_slider.pack(fill=tk.Y, expand=True, pady=5)   

        self.min_slider = ttk.Scale(
        self.slider_frame, from_=self.global_max, 
        to=self.global_min,
        orient=tk.VERTICAL, command=self.on_min_slide
        ) 
        self.min_slider.pack(fill=tk.Y, expand=True, pady=5)
        self.min_label = ttk.Label(self.slider_frame, text=f"Min value: {self.global_min}", font=("Arial", 10, "bold"))
        self.min_label.pack(pady=5)        

        self.max_slider.set(self.global_max)
    

    def get_filter_column(self, phase=None):
        """Get the column to filter based on plot type and phase"""
        if phase is None:
            phase = '1'  # Default to phase 1 if no phase is provided
        if self.plot_type == "Voltage":
            return f"voltagemoy{phase[-1]}"
        elif self.plot_type == "Current":
            return f"currentmoy{phase[-1]}"          
        else:
            return f"powermoy{phase[-1]}"

    def get_column_names(self):
        """Get the column names based on plot type"""
        if self.plot_type == "Voltage":
            return ["voltagemoy1", "voltagemoy2", "voltagemoy3", "voltagemoy4"]
        elif self.plot_type == "Current":
            return ["currentmoy1", "currentmoy2", "currentmoy3", "currentmoy4"]
        else:  # Power
            return ["powermoy1", "powermoy2", "powermoy3", "powermoy4"]

    def on_min_slide(self, value):
        """Handle minimum slider movement"""
        self.min_label.config(text=f"Min value: {float(value):.2f}")
        self.update_filtered_data()

    def on_max_slide(self, value):
        """Handle maximum slider movement"""
        self.max_label.config(text=f"Max value: {float(value):.2f}")
        self.update_filtered_data()

    def update_filtered_data(self):
        """Filter data based on slider value"""
        upper_val = self.max_slider.get()
        lower_val = self.min_slider.get()
        
        # Use the smaller value as min and larger as max
        min_val = min(upper_val, lower_val)
        max_val = max(upper_val, lower_val)
        
        # Get the selected phases
        self.selected_phases = [phase for phase, var in self.phase_visibility.items() if var.get()]
        
        # Get the filter columns based on the selected phases
        columns = [self.get_filter_column(phase=phase[-1]) for phase in self.selected_phases]
        
        # Filter the data for each selected phase
        filtered_data = self.data.copy()       
                    
        for column in columns:
            filtered_data = filtered_data[(filtered_data[column] >= min_val) & (filtered_data[column] <= max_val)]
            
        self.filtered_data = filtered_data
        
        # Update max and min values                                 
        self.max_value_var.set(f"Max: {float(max_val):.2f}")
        self.min_value_var.set(f"Min: {float(min_val):.2f}")
        
        self.update_plot()    

    def update_plot(self):
        """Update the plot with current time range"""
        try:
            # Get time range
            start_time = pd.to_datetime(self.start_var.get())
            end_time = pd.to_datetime(self.end_var.get())

            # Calculate time elapsed
            time_elapsed = end_time - start_time
            self.time_elapsed_var.set(f"Time Elapsed: {time_elapsed}")

            # Filter data
            mask = (self.filtered_data['time'] >= start_time) & (self.filtered_data['time'] <= end_time)
            plot_data = self.filtered_data.loc[mask]

            if plot_data.empty:
                self.points_var.set("Points: 0")
                return

            # Update points counter
            num_points = len(plot_data)
            self.points_var.set(f"Points: {num_points:,}")

            # Clear plot
            self.ax.clear()

            # Plot data for each phase
            columns = self.get_column_names()
            colors = ['blue', 'red', 'green','grey']
            labels = ['Phase 1', 'Phase 2', 'Phase 3','Phase 4']
            
            total_energy = 0 # Initialisation de total_energy

            for col, color, label in zip(columns, colors, labels):
                if self.phase_visibility[label].get():  # Only plot if phase is visible
                    # Plot the line
                    self.ax.plot(plot_data['time'], plot_data[col], 
                                color=color, label=label, linewidth=1)
                    
                    # Calculate and display average 
                    avg_value = plot_data[col].mean()                        
                    # Add horizontal line for average
                    self.ax.axhline(y=avg_value, color=color, linestyle='--', alpha=0.5)

                    # Add text annotation for average
                    self.ax.annotate(
                        f'Avg {label}: {avg_value:.2f}',
                        xy=(0.02, 0.98 - (0.05 * list(columns).index(col))),  # Position text at top-left, stacked
                        xycoords='axes fraction',
                        color=color,
                        bbox=dict(boxstyle='round,pad=0.5', facecolor='white', alpha=0.8),
                        verticalalignment='top'
                    )
                    
                    # Mise  à jour les labels Max and Min                                
                    max_idx = plot_data[col].idxmax()  # This returns the index du maximum dans la colone col
                    max_time = plot_data['time'].loc[max_idx]  # Use .loc to access by index label instead of position
                    datetime_str = max_time.strftime('%d/%m %H:%M:%S')             
                    self.max_value_var.set(f"Max: {float(plot_data[col].max()):.2f}"+f" ({datetime_str})")   
                     
                    self.ax.plot(max_time, plot_data[col].max(), 'o', color=color, markeredgecolor='black', markerfacecolor='purple', markersize=6)                     
                                            
                    min_idx = plot_data[col].idxmin()  # This returns the index label
                    min_time = plot_data['time'].loc[min_idx]  # Use .loc to access by index label instead of position
                    datetime_str = min_time.strftime('%d/%m %H:%M:%S') 
                    self.min_value_var.set(f"Min: {float(plot_data[col].min()):.2f}"+f" ({datetime_str})")  
                      
                    self.ax.plot(min_time, plot_data[col].min(), 'o', color=color, markeredgecolor='black', markerfacecolor='yellow', markersize=6)                                                                               
            
                    # Calculate energy for the phase
                    if self.plot_type=="Power":
                        time_sec = plot_data['time'].astype(np.int64) / 1e9  # Convert nanoseconds to seconds
                        time_diff = np.diff(time_sec)  # Compute time differences (in seconds)
                        power_values = plot_data[col].values
                        energy = np.sum((power_values[:-1] + power_values[1:]) / 2 * time_diff) / 3600000  # Convert to kWh
                        if col!="powermoy4":
                            total_energy += energy
                        else:
                            total_energy=energy
                # ****************************************Ajout du tracé moyenne glissante
                # Calculate and display average  
                    if self.mean_var.get():  
                        nombre_points=int(self.input_field.get())
                        signal_lisse = self.lissage(plot_data[col],nombre_points)
            
                        self.ax.plot(plot_data['time'], signal_lisse, 
                                color="purple", label="moyenne glissante"+label, linewidth=1.5)
                            
                if self.plot_type=="Power":
                    self.energy_var.set(f"Energy: {total_energy:.2f} kWh")
                                                       
                # Configure plot
                self.ax.set_title(f'{self.plot_type} Comparison - All Phases')
            
            self.ax.set_ylabel(f'{self.plot_type} ' + 
                             ('(V)' if self.plot_type == 'Voltage' else 
                              '(A)' if self.plot_type == 'Current' else '(W)'))
            self.ax.grid(True)
            self.ax.legend()

            # Format x-axis
            self.ax.xaxis.set_major_formatter(mdates.DateFormatter('%d/%m %H:%M:%S'))
            self.ax.tick_params(axis='x', rotation=30,  labelsize=8)     

            # Update display
            self.fig.tight_layout()
            self.canvas.draw()

        except Exception as e:
            # messagebox.showerror("Plot Error", f"Error creating plot: {str(e)}")
            raise
        
    def on_start_slide(self, value):
        """Handle start slider movement"""
        # self.min_time = self.data['time'].min()       
        seconds = float(value)
        if seconds < self.end_slider.get():
            new_time = self.min_time + pd.Timedelta(seconds=int(seconds))
            self.start_var.set(new_time.strftime('%Y-%m-%d %H:%M:%S'))
            self.update_plot()
        else:
            self.start_slider.set(self.end_slider.get() - 1)

    def on_end_slide(self, value):
        """Handle end slider movement"""
        # self.min_time = self.data['time'].min()             
        seconds = float(value)
        if seconds > self.start_slider.get():
            new_time = self.min_time + pd.Timedelta(seconds=int(seconds))
            self.end_var.set(new_time.strftime('%Y-%m-%d %H:%M:%S'))           
            self.update_plot()
        else:
            self.end_slider.set(self.start_slider.get() + 1)

    def reset_range(self):
        """Reset time range to show all data"""
        self.start_var.set(self.min_time.strftime('%Y-%m-%d %H:%M:%S'))
        self.end_var.set(self.max_time.strftime('%Y-%m-%d %H:%M:%S'))
        self.start_slider.set(0)
        self.end_slider.set(self.total_seconds)
        self.min_slider.set(self.global_min)
        self.max_slider.set(self.global_max)
        self.points_var.set(f"Points: {len(self.data):,}")
        self.update_plot()

    def get_visible_value(self):
        """Calculate min and max value based on visible phases"""
        columns = []
        for phase, var in self.phase_visibility.items():
            if var.get():  # If phase is visible
                if phase == 'Phase 1':
                    columns.append(self.get_column_names()[0])
                elif phase == 'Phase 2':
                    columns.append(self.get_column_names()[1])
                elif phase == 'Phase 3':
                    columns.append(self.get_column_names()[2])
                elif phase == 'Phase 4':
                    columns.append(self.get_column_names()[3])                    
        
        if not columns:  # If no phases are visible
            return self.global_min, self.global_max
        
        visible_min = self.data[columns].min().min()
        visible_max = self.data[columns].max().max()
        return visible_min, visible_max

    def update_slider_ranges(self):
        """Update slider ranges based on visible phases"""
        min_val, max_val = self.get_visible_value()
        
        # Store current positions as percentages
        old_range = self.max_slider.cget('to') - self.max_slider.cget('from')
        min_percent = (self.min_slider.get() - self.min_slider.cget('to')) / old_range if old_range != 0 else 0
        max_percent = (self.max_slider.get() - self.max_slider.cget('from')) / old_range if old_range != 0 else 1
        
        # Update slider configurations
        self.max_slider.configure(from_=max_val, to=min_val)        
        self.min_slider.configure(from_=max_val, to=min_val)

        
        # Set new values maintaining relative positions
        new_range = max_val - min_val
        self.max_slider.set(max_val + (max_percent * new_range))
        self.min_slider.set(min_val + (min_percent * new_range))        
        
        # Update labels
        self.min_label.config(text=f"Min value: {float(self.min_slider.get()):.2f}")
        self.max_label.config(text=f"Max value: {float(self.max_slider.get()):.2f}")

    def on_phase_toggle(self):
        """Handle phase visibility toggle"""
        self.update_slider_ranges()
        self.update_plot()


class PowerMonitorApp:
            
    def __init__(self):
        self.versionning = "       Michel ESPARSA\nVersion 2.1 du 01/03/2025"
        self.last_version = "Michel ESPARSA - Version 2.1 du 01/03/2025\n"\
        "- Création de checkbox des fenêtres à afficher\n"\
        "- Intégration du logo au fichier source\n"\
        "- Ajout de la fonctionalité 'phase4'\n"\
        "- Ajout de Min et Max aux fenêtres Comparaison\n"\
        "- Ajout de Min et Max aux fenêtre de Phases\n"\
        "- Ajout de marqueurs max et min aux fenêtres de Comparaison\n"\
        "- Ajout de la moyenne glissante\n"\
        "- Ajout du jour aux axes des abscisses et réduction de la police\n"\
        "Michel ESPARSA - Version 2.2 du 08/03/2025\n"\
        "- Ajout de la fonctionnalité de calendrier\n"\
        "- Inversion des sliders de valeurs\n"\
        " -Ajout du suivi du versionning"

        self.root = tk.Tk()
        self.root.title("Power Monitor")
        self.root.geometry("400x400") 
        self.root.resizable(False, False)        
        # First decode the base64 string into binary data
        decoded_data = base64.b64decode(resources.bolt64x64)
        # Then create an image from the binary data
        self.image = Image.open(io.BytesIO(decoded_data))
        # Convert PIL image to Tkinter PhotoImage qui sera reutilisé plus loin
        self.photo = ImageTk.PhotoImage(self.image)
        # Set the window icon
        self.root.iconphoto(False, self.photo)

        # Create main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Add logo
        img = ImageTk.PhotoImage(self.image)
        logo_label = ttk.Label(main_frame, image=img)
        logo_label.image = img # Keep a reference!
        logo_label.pack(pady=5)

        # Ajouter un error label permettant d'identifier les erreurs
        self.error_label = ttk.Label(main_frame, text="", foreground="red", wraplength=350)
        self.error_label.pack(pady=5)

        author_label = ttk.Label(main_frame, text=self.versionning, font=('Arial', 9, 'italic'))
        author_label.pack(pady=5)
        
        # Crée la barre des menus   
        self.create_menu()      
        
        # Create checkboxes for phases and comparison windows          
        self.create_display_options(main_frame)
        
        # Add load button
        load_btn = ttk.Button(main_frame, text="Load File", command=self.load_file)
        load_btn.pack(pady=10)
        
    def create_menu(self): 
        #Creer un menu
        menu_bar=tk.Menu(self.root)

        # File menu
        file_menu = tk.Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Open", command=self.load_file)
        file_menu.add_command(label="Exit", command=self.root.quit)

        # Help menu
        help_menu = tk.Menu(menu_bar, tearoff=0)
        help_menu.add_command(label="About", command=lambda: messagebox.showinfo("A propos",  self.last_version))
        menu_bar.add_cascade(label="Help", menu=help_menu)
        self.root.config(menu=menu_bar)        
        
    def create_display_options(self, parent):
        """Create checkbox options for display selection"""
        # Create frame for display options
        options_frame = ttk.LabelFrame(parent, text="Options d'affichage", padding="10")
        options_frame.pack(fill=tk.X, pady=10)
        
        # Create a container frame for horizontal layout
        container_frame = ttk.Frame(options_frame)
        container_frame.pack(fill=tk.X, pady=5)
        
        # Phase windows selection - now with side=tk.LEFT
        phase_frame = ttk.Frame(container_frame)
        phase_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 70))
        
        ttk.Label(phase_frame, text="Phase Windows:", font=('Arial', 10, 'bold')).pack(anchor=tk.W, pady=5)
        
        # Add checkboxes for phases
        self.phase_vars = {}
        for phase in range(1, 4):
            var = tk.BooleanVar(value=False)  # Default: all phases checked
            self.phase_vars[phase] = var
            cb = ttk.Checkbutton(
                phase_frame,
                text=f"Phase {phase}",
                variable=var
            )
            cb.pack(anchor=tk.W, padx=15)
        
        # Comparison windows selection - now with side=tk.LEFT
        comparison_frame = ttk.Frame(container_frame)
        comparison_frame.pack(side=tk.LEFT, fill=tk.Y)
        
        ttk.Label(comparison_frame, text="Comparison Windows:", font=('Arial', 10, 'bold')).pack(anchor=tk.W, pady=5)
        
        # Add checkboxes for comparison types
        self.comparison_vars = {}
        for comp_type in ["Voltage", "Current", "Power"]:
            var = tk.BooleanVar(value=False)  # Default: all comparisons checked
            self.comparison_vars[comp_type] = var
            cb = ttk.Checkbutton(
                comparison_frame,
                text=comp_type,
                variable=var
            )
            cb.pack(anchor=tk.W, padx=15)
        self.comparison_vars["Power"].set(True)  # Default to Power comparison"]            
            
    def create_phase_window(self, phase_num, data):
        # Create new window for phase
        phase_window = tk.Toplevel(self.root)
        phase_window.title(f"Phase {phase_num}")
        phase_window.geometry("1100x800")
        phase_window.iconphoto(False, self.photo)
        
        # Create main container
        main_frame = ttk.Frame(phase_window, padding="5")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Calculate time range
        data['time'] = pd.to_datetime(data['time'], format='%d/%m/%Y %H:%M:%S')
        min_time = data['time'].min()
        max_time = data['time'].max()
        total_seconds = int((max_time - min_time).total_seconds())
        
        # Time selection frame
        time_frame = ttk.LabelFrame(main_frame, text="Time Range Selection", padding="5")
        time_frame.pack(fill=tk.X, pady=5)
        
        # Time entry frame
        entry_frame = ttk.Frame(time_frame)
        entry_frame.pack(fill=tk.X, pady=5)
        
        # Start time entry
        ttk.Label(entry_frame, text="Start:").pack(side=tk.LEFT, padx=5)
        start_var = tk.StringVar(value=min_time.strftime('%Y-%m-%d %H:%M:%S'))
        start_entry = ttk.Entry(entry_frame, textvariable=start_var, width=20)
        start_entry.pack(side=tk.LEFT, padx=5)
        
        # End time entry
        ttk.Label(entry_frame, text="End:").pack(side=tk.LEFT, padx=5)
        end_var = tk.StringVar(value=max_time.strftime('%Y-%m-%d %H:%M:%S'))
        end_entry = ttk.Entry(entry_frame, textvariable=end_var, width=20)
        end_entry.pack(side=tk.LEFT, padx=5)
        
        #------------------------ Points counter
        points_var = tk.StringVar(value=f"Points: {len(data):,}")
        ttk.Label(entry_frame, textvariable=points_var, font=('Arial', 10, 'bold')).pack(side=tk.LEFT, padx=15)
        
        # -----------------------Time elapsed label
        time_elapsed_var = tk.StringVar(value=f"Time Elapsed: {total_seconds}s")
        ttk.Label(entry_frame, textvariable=time_elapsed_var, font=('Arial', 10, 'bold')).pack(side=tk.LEFT, padx=15)
        
        # Time elapsed in days, hours, minutes, and seconds
        time_elapsed_dhms_var = tk.StringVar(value="Time Elapsed: --")
        ttk.Label(entry_frame, textvariable=time_elapsed_dhms_var, font=('Arial', 10, 'bold')).pack(side=tk.LEFT, padx=15)
        

        def update_labels():
            start_time = pd.to_datetime(start_var.get(), format='%Y-%m-%d %H:%M:%S')
            end_time = pd.to_datetime(end_var.get(), format='%Y-%m-%d %H:%M:%S')
            filtered_data = data[(data['time'] >= start_time) & (data['time'] <= end_time)]
            points_var.set(f"Points: {len(filtered_data):,}")
            elapsed_seconds = int((end_time - start_time).total_seconds())
            time_elapsed_var.set(f"Time Elapsed: {elapsed_seconds}s")

            # Calculate days, hours, minutes, and seconds
            days, remainder = divmod(elapsed_seconds, 86400)
            hours, remainder = divmod(remainder, 3600)
            minutes, seconds = divmod(remainder, 60)
            time_elapsed_dhms_var.set(f"Time Elapsed: {days}d {hours}h {minutes}m {seconds}s")

        start_var.trace_add("write", lambda *args: update_labels())
        end_var.trace_add("write", lambda *args: update_labels())
        
        # Average values display frame
        avg_frame = ttk.LabelFrame(main_frame, text="Main Values", padding="5")
        avg_frame.pack(fill=tk.X, pady=5)
        
        # Labels for average values
        voltage_avg_var = tk.StringVar(value="Voltage Average: --")
        current_avg_var = tk.StringVar(value="Current Average: --")
        power_avg_var = tk.StringVar(value="Power Average: --")
        energy_var = tk.StringVar(value="Energy: -- kWh")
        
        ttk.Label(avg_frame, textvariable=voltage_avg_var, font=('Arial', 10, 'bold')).pack(side=tk.LEFT, padx=15)
        ttk.Label(avg_frame, textvariable=current_avg_var, font=('Arial', 10, 'bold')).pack(side=tk.LEFT, padx=15)
        ttk.Label(avg_frame, textvariable=power_avg_var, font=('Arial', 10, 'bold')).pack(side=tk.LEFT, padx=15)
        ttk.Label(avg_frame, textvariable=energy_var, font=('Arial', 10, 'bold')).pack(side=tk.LEFT, padx=15)        
        
        # Labels for max values
        voltage_max_var = tk.StringVar(value="Voltage Max: --")
        current_max_var = tk.StringVar(value="Current Max: --")
        power_max_var = tk.StringVar(value="Power Max: --")
        ttk.Label(avg_frame, textvariable=voltage_max_var, font=('Arial', 10, 'bold')).pack(side=tk.LEFT, padx=15)
        ttk.Label(avg_frame, textvariable=current_max_var, font=('Arial', 10, 'bold')).pack(side=tk.LEFT, padx=15)
        ttk.Label(avg_frame, textvariable=power_max_var, font=('Arial', 10, 'bold')).pack(side=tk.LEFT, padx=15)    
         
        # Labels for min values (seulement power)
        power_min_var = tk.StringVar(value="Power Min: --")
        ttk.Label(avg_frame, textvariable=power_min_var, font=('Arial', 10, 'bold')).pack(side=tk.LEFT, padx=15)                
                        
        # Slider frame
        slider_frame = ttk.Frame(time_frame)
        slider_frame.pack(fill=tk.X, pady=5)
        
        # Create figure and plots
        fig = Figure(figsize=(12, 10))
        fig.subplots_adjust(bottom=0.15, hspace=0.4)
        voltage_ax = fig.add_subplot(311)
        current_ax = fig.add_subplot(312)
        power_ax = fig.add_subplot(313)
        
        canvas = FigureCanvasTkAgg(fig, main_frame)
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, pady=5)
        
        toolbar = NavigationToolbar2Tk(canvas, main_frame)
        toolbar.update()
        
        status_bar = ttk.Label(main_frame, text="", relief=tk.SUNKEN)
        status_bar.pack(fill=tk.X, pady=5)
        
        # Function to update plots
        def update_plots():
            try:
                start_time = pd.to_datetime(start_var.get())
                end_time = pd.to_datetime(end_var.get())
                
                # Filter data
                mask = (data['time'] >= start_time) & (data['time'] <= end_time)
                plot_data = data.loc[mask]
                
                # Clear plots
                voltage_ax.clear()
                current_ax.clear()
                power_ax.clear()
                
                # Suffix for column names
                suffix = str(phase_num)
                
                # Calculate and update averages
                voltage_avg = plot_data[f'voltagemoy{suffix}'].mean()
                current_avg = plot_data[f'currentmoy{suffix}'].mean()
                power_avg = plot_data[f'powermoy{suffix}'].mean()
                
                voltage_avg_var.set(f"Voltage Average: {voltage_avg:.2f} V")
                current_avg_var.set(f"Current Average: {current_avg:.2f} A")
                power_avg_var.set(f"Power Average: {power_avg:.0f} W")
                            
                # Mise  à jour les labels Max and Min                                
                max_idx = plot_data[f'voltagemoy{suffix}'].idxmax()  # This returns the index label
                max_time = plot_data['time'].loc[max_idx]  # Use .loc to access by index label instead of position
                datetime_str = max_time.strftime('%d/%m %H:%M:%S')       
                voltage_max_var.set(f"Volatge Max: {float(plot_data[f'voltagemoy{suffix}'].max()):.2f} V"+f" ({datetime_str})")   

                max_idx = plot_data[f'currentmoy{suffix}'].idxmax()  # This returns the index label
                max_time = plot_data['time'].loc[max_idx]  # Use .loc to access by index label instead of position
                datetime_str = max_time.strftime('%d/%m %H:%M:%S')       
                current_max_var.set(f"Current Max: {float(plot_data[f'currentmoy{suffix}'].max()):.2f} A"+f" ({datetime_str})")   
                
                max_idx = plot_data[f'powermoy{suffix}'].idxmax()  # This returns the index label
                max_time = plot_data['time'].loc[max_idx]  # Use .loc to access by index label instead of position
                datetime_str = max_time.strftime('%d/%m %H:%M:%S')       
                power_max_var.set(f"Power Max: {float(plot_data[f'powermoy{suffix}'].max()):.2f} W"+f" ({datetime_str})")                   
                
                min_idx = plot_data[f'powermoy{suffix}'].idxmin()  # This returns the index label
                min_time = plot_data['time'].loc[min_idx]  # Use .loc to access by index label instead of position
                datetime_str = min_time.strftime('%d/%m %H:%M:%S')       
                power_min_var.set(f"Power Min: {float(plot_data[f'powermoy{suffix}'].min()):.2f} W"+f" ({datetime_str})")                                    
                               
                voltage_avg = plot_data[f'voltagemoy{suffix}'].mean()
                current_avg = plot_data[f'currentmoy{suffix}'].mean()
                power_avg = plot_data[f'powermoy{suffix}'].mean()
                
                voltage_avg_var.set(f"Voltage Average: {voltage_avg:.2f} V")
                current_avg_var.set(f"Current Average: {current_avg:.2f} A")
                power_avg_var.set(f"Power Average: {power_avg:.0f} W")                

                # Calculate energy in kWh using trapezoidal rule
                # Step 1: Convert time to seconds and compute time differences
                time_sec = plot_data['time'].astype(np.int64) / 1e9  # Convert nanoseconds to seconds
                time_diff = np.diff(time_sec)  # Compute time differences (in seconds)

                # Step 2: Extract power values
                power_values = plot_data[f'powermoy{suffix}'].values

                # Step 3: Perform numerical integration using time differences
                # Align power_values with time_diff (exclude the last power value)

                energy = np.sum((power_values[:-1] + power_values[1:]) / 2 * time_diff) / 3600000  # Convert to kWh

                # Step 4: Update energy variable
                energy_var.set(f"Energy: {energy:.2f} kWh")

                # Plot voltage with average line
                voltage_ax.plot(plot_data['time'], plot_data[f'voltagemoy{suffix}'], 
                            'b-', linewidth=1, label='Voltage')
                voltage_ax.axhline(y=voltage_avg, color='r', linestyle='--', 
                                label=f'Avg: {voltage_avg:.2f}V')
                voltage_ax.set_title(f'Voltage - Phase {phase_num}')
                voltage_ax.set_ylabel('Voltage (V)')
                voltage_ax.grid(True)
                voltage_ax.legend()
                
                # Plot current with average line
                current_ax.plot(plot_data['time'], plot_data[f'currentmoy{suffix}'], 
                            'r-', linewidth=1, label='Current')
                current_ax.axhline(y=current_avg, color='b', linestyle='--', 
                                label=f'Avg: {current_avg:.2f}A')
                current_ax.set_title(f'Current - Phase {phase_num}')
                current_ax.set_ylabel('Current (A)')
                current_ax.grid(True)
                current_ax.legend()
                
                # Plot power with average line
                power_ax.plot(plot_data['time'], plot_data[f'powermoy{suffix}'], 
                            'g-', linewidth=1, label='Power')
                power_ax.axhline(y=power_avg, color='r', linestyle='--', 
                            label=f'Avg: {power_avg:.0f}W')
                power_ax.set_title(f'Power - Phase {phase_num}')
                power_ax.set_ylabel('Power (W)')
                power_ax.grid(True)
                power_ax.legend()
                
                # Format x-axis
                for ax in [voltage_ax, current_ax, power_ax]:
                    ax.xaxis.set_major_formatter(mdates.DateFormatter('%d/%m %H:%M:%S'))
                    ax.tick_params(axis='x', rotation=30,  labelsize=8)
                
                canvas.draw()
                status_bar.config(
                    text=f"Showing data from {start_time.strftime('%Y-%m-%d %H:%M:%S')} "
                        f"to {end_time.strftime('%Y-%m-%d %H:%M:%S')}"
                )
                
            except Exception as e:
                messagebox.showerror("Error", f"Error updating plots: {str(e)}")
        
        def on_start_slide(value):
            seconds = float(value)
            if seconds < end_slider.get():
                new_time = min_time + pd.Timedelta(seconds=int(seconds))
                start_var.set(new_time.strftime('%Y-%m-%d %H:%M:%S'))
                update_plots()
            else:
                start_slider.set(end_slider.get() - 1)
        
        def on_end_slide(value):
            seconds = float(value)
            if seconds > start_slider.get():
                new_time = min_time + pd.Timedelta(seconds=int(seconds))
                end_var.set(new_time.strftime('%Y-%m-%d %H:%M:%S'))
                update_plots()              
            else:
                end_slider.set(start_slider.get() + 1)
        
        def reset_range():
            start_var.set(min_time.strftime('%Y-%m-%d %H:%M:%S'))
            end_var.set(max_time.strftime('%Y-%m-%d %H:%M:%S'))
            start_slider.set(0)
            end_slider.set(total_seconds)
            update_plots()
       
        # Start slider
        ttk.Label(slider_frame, text="Start Time:").pack(side=tk.LEFT, padx=5)
        start_slider = ttk.Scale(slider_frame, from_=0, to=total_seconds, 
                            orient=tk.HORIZONTAL, command=on_start_slide)
        start_slider.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        # End slider
        end_frame = ttk.Frame(time_frame)
        end_frame.pack(fill=tk.X, pady=2)
        ttk.Label(end_frame, text="End Time:").pack(side=tk.LEFT, padx=5)
        end_slider = ttk.Scale(end_frame, from_=0, to=total_seconds, 
                            orient=tk.HORIZONTAL, command=on_end_slide)
        end_slider.set(total_seconds)
        end_slider.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        # Button
        ttk.Button(entry_frame, text="Reset", command=reset_range).pack(side=tk.LEFT, padx=5)        
            
        # Initial plot
        update_plots()

    def load_file(self):
        try:
            # Open file dialog
            file_path = filedialog.askopenfilename(
                title="Select File",
                filetypes=[("txt files", "*.txt"),("CSV files", "*.csv"),("All files", "*.*")]
            )
            
            if not file_path:
                return
            
            # Read CSV file
            data = pd.read_csv(file_path, sep=';')
            
            # Create individual phase windows based on checkbox selection
            for phase in range(1, 4):
                if self.phase_vars[phase].get():
                    self.create_phase_window(phase, data)
            
            # Create comparison windows based on checkbox selection
            for comp_type in ["Voltage", "Current", "Power"]:
                if self.comparison_vars[comp_type].get():
                    ComparisonWindow(self.root, data, comp_type)
            
            self.error_label.config(text="")
            
        except Exception as e:
            self.error_label.config(text=f"Error: {str(e)}")
    
    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = PowerMonitorApp()
    app.run()
