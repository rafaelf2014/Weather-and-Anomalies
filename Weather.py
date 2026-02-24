import tkinter as tk
from tkinter import ttk
import customtkinter
from tkinter import messagebox
import requests
from tkinter import PhotoImage
from datetime import datetime
import os
import matplotlib.pyplot as plt
import pystray
from pystray import MenuItem as item
from PIL import Image, ImageDraw
import threading
import sys
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

############constants#################
HIST_PLACE_FILENAME = "hist_place.txt"
EMAIL_SAVE = "email.txt"
API_KEY = ''
######################################

###############READ FILES#################
with open(HIST_PLACE_FILENAME, "r") as file:
    hist_place = file.read().strip()

with open(EMAIL_SAVE, "r") as efile:
    email = efile.read().strip()
##########################################

#Basic appearence
customtkinter.set_appearance_mode("System") 
customtkinter.set_default_color_theme("dark-blue")  



class App(customtkinter.CTk):
    def __init__(self):
        super().__init__()

        ########WINDOW CONFIGURATION#############
        self.title("Tempo")
        self.initial_width = 600
        self.initial_height = 170
        self.geometry(f"{self.initial_width}x{self.initial_height}")
        self.resizable(False, False)
        self.iconbitmap("icons/app.ico")
        ##########################################

        self.email = ""
        self.last_email_sent = None
        self.disaster_hist = 0


        #layout do grid
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(1, weight=1)

        #empty label, é só pra criar espaço
        self.empty_label = customtkinter.CTkLabel(self, text="")
        self.empty_label.grid(row=0, column=0, columnspan=3, padx=20, pady=(0, 0))

        #label de titulo para a caixa de pesquisa
        self.title_label = customtkinter.CTkLabel(self, text="Choose a location", font=customtkinter.CTkFont(size=30, weight="bold"))
        self.title_label.grid(row=0, column=0, columnspan=3, padx=20, pady=(20,0))

        #barra de pesquisa com bind no ENTER
        self.search_bar = customtkinter.CTkEntry(self, placeholder_text="Search...")
        self.search_bar.grid(row=1, column=1, padx=(20, 10), pady=(30, 0), sticky="ew")
        self.search_bar.bind("<Return>", self.store_search)

        #search button
        self.search_button = customtkinter.CTkButton(self, text="Search", command=self.store_search)
        self.search_button.grid(row=1, column=2, padx=(10, 20), pady=(30, 0))

        #Side bar with 3 buttons
        self.sidebar_frame = customtkinter.CTkFrame(self, width=140, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, rowspan=10, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(4, weight=1)
        self.logo_label = customtkinter.CTkLabel(self.sidebar_frame, text="Options", font=customtkinter.CTkFont(size=20, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))
        self.sidebar_button_1 = customtkinter.CTkButton(self.sidebar_frame, text="Today", command=self.back_to_today)
        self.sidebar_button_1.grid(row=1, column=0, padx=20, pady=10)
        self.sidebar_button_2 = customtkinter.CTkButton(self.sidebar_frame, text="Weekly", command=self.show_weekly_weather)
        self.sidebar_button_2.grid(row=2, column=0, padx=20, pady=10)
        self.sidebar_button_3 = customtkinter.CTkButton(self.sidebar_frame, text="History", command=self.show_weather_history)
        self.sidebar_button_3.grid(row=3, column=0, padx=20, pady=10)

        #2 more buttons for the side bar, added after history function
        self.show_search_button = customtkinter.CTkButton(self.sidebar_frame, text="Change Recording", command=self.open_search_popup, width=12, height=1)
        self.show_search_button.grid(row=6, column=0, padx=20, pady=(0, 10), sticky="n")

        self.notifications_button = customtkinter.CTkButton(self.sidebar_frame, text="Notifications", command=self.open_notifications)
        self.notifications_button.grid(row=4, column=0, padx=20, pady=(0, 0), sticky="n")

        #dropdown menu for dark/light mode
        self.appearance_mode_label = customtkinter.CTkLabel(self.sidebar_frame, text="Appearance Mode:", anchor="w")
        self.appearance_mode_label.grid(row=7, column=0, padx=20, pady=(0, 0))
        self.appearance_mode_optionemenu = customtkinter.CTkOptionMenu(self.sidebar_frame, values=["Light", "Dark", "System"], command=self.change_appearance_mode_event)
        self.appearance_mode_optionemenu.grid(row=8, column=0, padx=20, pady=(10, 10))
        self.appearance_mode_optionemenu.set("Dark")

        # Hide sidebar before search is done
        self.sidebar_frame.grid_remove()

        # Placeholder for current weather image
        self.weather_image_label = customtkinter.CTkLabel(self, text='')
        self.weather_image_label.grid(row=0, column=4, rowspan=4, padx=(10, 10), pady=(10, 0), sticky="nsew")
        self.history_label = customtkinter.CTkLabel(self.sidebar_frame, text=f"Recording: {hist_place}", font=customtkinter.CTkFont(size=12))
        self.history_label.grid(row=5, column=0, padx=20, pady=(0, 0), sticky="n")

        #asdasda
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.create_tray_icon()

    #creation of the notifications window
    def open_notifications(self):
        self.notification_window = customtkinter.CTkToplevel(self)
        self.notification_window.title("Notifications")
        self.notification_window.geometry("300x200")
        
        self.email_label = customtkinter.CTkLabel(self.notification_window, text=f"Email: {email}")
        self.email_label.pack(pady=10)
        self.email_entry = customtkinter.CTkEntry(self.notification_window)
        self.email_entry.pack(pady=10)
        self.save_button = customtkinter.CTkButton(self.notification_window, text="Save", command=self.save_email)
        self.save_button.pack(pady=10)
        self.test_button = customtkinter.CTkButton(self.notification_window, text="Test", command=self.send_test_email)
        self.test_button.pack(pady=10)

    #Saves the email to a file for storing purposes
    def save_email(self):
        email = self.email_entry.get()
        with open("email.txt", "w") as file:
            file.write(email)
        self.email_label.configure(text=f"Current email: {email}")
    
    #Simple test function, por favor checkem o spam 99% das vezes vai la parar    
    def send_test_email(self):
        if email:
            self.send_email(email, "Test Email", "This is a test email from the Weather App.")
            messagebox.showinfo("Success", "Test email sent successfully")
        else:
            messagebox.showerror("Error", "Please enter a valid email address")
    
    #sends email when condtions are met, one per day
    def check_and_send_email(self):
        current_time = datetime.now()
        if self.last_email_sent is None or current_time - self.last_email_sent > timedelta(days=1):
            self.send_email(email, "Disaster Alert", "Disaster probabilities exceeded 50%.")
            self.last_email_sent = current_time

    #just to send emails
    def send_email(self, to_email, subject, body):
        from_email = "labprojectgroup102@outlook.pt"
        from_password = "group102lab"
        message = MIMEMultipart()
        message['From'] = from_email
        message['To'] = to_email
        message['Subject'] = subject
        message.attach(MIMEText(body, 'plain'))
        
        try:
            with smtplib.SMTP('smtp.office365.com', 587) as server:
                server.starttls()
                server.login(from_email, from_password)
                text = message.as_string()
                server.sendmail(from_email, to_email, text)
            print(f"Email sent to {to_email}")  # Debugging line
        except smtplib.SMTPException as e:
            print(f"Error: {e}")  # Debugging line
            messagebox.showerror("Error", f"SMTP error occurred: {e}")
        except Exception as e:
            print(f"General error: {e}")  # Debugging line
            messagebox.showerror("Error", f"An error occurred: {e}")

####### instead of the app closing, it coes to second plane #############################################
    def on_closing(self):
        self.withdraw()
        self.tray_icon.run_detached()

    #cria um icone que aparece naquela setinha ao lado das horas, não me lembro do nome daquilo
    def create_tray_icon(self):
        # Load custom .ico file for the system tray icon
        icon_image_path = "icons/app.ico"  # Change to your .ico file path
        icon_image = Image.open(icon_image_path)

        menu = (
            item('Open', self.show_window),
            item('Exit', self.exit_app)
        )
        
        self.tray_icon = pystray.Icon("Weather App", icon_image, "Weather App", menu)

    #restaura a janela
    def show_window(self):
        self.deiconify()
        self.tray_icon.stop()

    #fecha a aplicação completamente
    def exit_app(self):
        def quit_app(icon, item):
            self.tray_icon.stop()
            self.quit()
        
        # Execute quit_app in a thread-safe manner
        self.after(0, quit_app, None, None)
########################################################################################################

########################## history function ###############################################3######
    #saves the place you want to record in a file
    def save_hist_place(self):
        with open(HIST_PLACE_FILENAME, "w") as file:
            file.write(hist_place)

    #opens a popup to select the place to record
    def open_search_popup(self):
        # Create a new window for the popup
        popup = tk.Toplevel(self)
        popup.title("Change Recording")

        # Set background color of the popup
        popup.configure(background="gray10")

        # Create entry for search bar in the popup
        search_bar_for_history = customtkinter.CTkEntry(popup, placeholder_text="Enter new recording...")
        search_bar_for_history.pack(padx=20, pady=10)

        # Create a label for error message
        error_label = customtkinter.CTkLabel(popup, text="", font=customtkinter.CTkFont(size=12))
        error_label.pack()

        # Bind the Enter key to update_hist_place and close the popup
        search_bar_for_history.bind("<Return>", lambda event: self.update_hist_place(search_bar_for_history.get(), popup, error_label))

    #change the recorded place
    def update_hist_place(self, new_value, popup, error_label):
        # Check if the new hist_place is a valid city
        if check_city_validity(new_value, API_KEY):
            # Update hist_place with the new value, update the label text, and save to file
            global hist_place
            hist_place = new_value.title()
            self.history_label.configure(text=f"Recording: {hist_place}")
            self.save_hist_place()
            popup.destroy()  # Close the popup after updating hist_place
        else:
            error_label.configure(text="Invalid city name. Please enter a valid city name.")
        self.store_hist()
#######################################################################################################

    #changes the appearence mode
    def change_appearance_mode_event(self, new_appearance_mode: str):
        customtkinter.set_appearance_mode(new_appearance_mode)
        self.store_search()

    #refreshes both main functions each minute, meaning you can let the app stay open and let it record and update the weather in real-time
    def schedule_refresh(self):
        self.after(60000, self.store_search)
        self.after(60000, self.store_hist)

    #registers the weather for the place selected to record, currently 1 time per day
    #, if we have spare time we can create a selector to change the time interval
    def store_hist(self, event=None):
        # Use hist_place instead of global_place
        global_place = hist_place.title()  # Convert the city name to title case
        current_temperature, humidity, pressure, wind_speed, weather_condition = get_weather_data(global_place, API_KEY)
        forecast_hist = get_weekly_forecast(global_place, API_KEY)
        disaster_hist = predict_weather_event(forecast_hist)

        if current_temperature is None:
            return

        with open("weather_history.txt", "r") as file:
            lines = file.readlines()
            if lines:
                last_line = lines[-1].split(",")
                last_date = last_line[1]
                last_place = last_line[0]
                current_date = datetime.now().strftime("%Y-%m-%d")
                if last_date == current_date and last_place == global_place:
                    # Data for the current date already exists, so ignore it
                    return

        # Append new data to the file
        with open("weather_history.txt", "a") as file:
            file.write(f"{global_place},{datetime.now().strftime('%Y-%m-%d')},{current_temperature},{humidity},{pressure},{wind_speed}\n")

        self.check_and_send_email()

    #opens the file where the history is located
    def show_weather_history(self):
        # Open the file in the default file explorer
        os.system("start weather_history.txt")

    #main fuction, shows today's weather
    def store_search(self, event=None):

        tempo = datetime.now()
        tempo_agr = tempo.strftime("%d-%m • %H:%M")

        # create title for the textbox
        self.textbox_title = customtkinter.CTkLabel(self, text=tempo_agr, font=customtkinter.CTkFont(size=24, weight="bold"))
        self.textbox_title.grid(row=0, column=2, columnspan=1, padx=0, pady=(20, 10))
        self.textbox_title.grid_remove()

        # Placeholder for weather image
        self.weather_image_label = customtkinter.CTkLabel(self, text='')
        self.weather_image_label.grid(row=1, column=4, rowspan=3, padx=(10, 10), pady=(10, 0), sticky="nsew")

        # Create back button
        self.back_button = customtkinter.CTkButton(self, text="◀", command=self.back_to_search, font=customtkinter.CTkFont(size=20), width=40, height=40 )
        self.back_button.grid(row=0, column=4, padx=(0, 90), pady=(20, 0), sticky="ne")
        self.back_button.grid_remove()


        global_place = self.search_bar.get().title()  # Convert the city name to title case
        current_temperature, humidity, pressure, wind_speed, weather_condition = get_weather_data(global_place, API_KEY)

        #checks if the place is valid
        if current_temperature is None:
            error_label = customtkinter.CTkLabel(self, text="City not found or API error", font=customtkinter.CTkFont(size=16, weight="bold"))
            error_label.grid(row=1, column=1, columnspan=3, padx=0, pady=(0,45))
            self.after(5000, error_label.destroy)  # Remove error message after 5 seconds
            return

        ################### gets the forecast and uses the algorithm to estimate disasters ##############
        forecast = get_weekly_forecast(global_place, API_KEY)
        disaster = predict_weather_event(forecast)
        #################################################################################################

        # Remove the old labels if they exist
        for widget in self.grid_slaves():
            if int(widget.grid_info()["row"]) > 1:
                widget.grid_forget()

        #changes the images depending on the appearence mode
        if customtkinter.get_appearance_mode() == "Light":
            # Update images to inverted versions for light mode
            self.humidity_image = PhotoImage(file='icons/humidity_inverted.png')
            self.pressure_image = PhotoImage(file="icons/pressure_inverted.png")
            self.wind_speed_image = PhotoImage(file="icons/wind_speed_inverted.png")
        else:
            # Use default images for other modes
            self.humidity_image = PhotoImage(file='icons/humidity.png')
            self.pressure_image = PhotoImage(file="icons/pressure.png")
            self.wind_speed_image = PhotoImage(file="icons/wind_speed.png")

        #makes the images 5x smaller
        self.humidity_image = self.humidity_image.subsample(5, 5)
        self.pressure_image = self.pressure_image.subsample(5, 5)
        self.wind_speed_image = self.wind_speed_image.subsample(5, 5)

        # Load the weather images
        img_path = {
            "Clear": "icons/clear.png",
            "Clouds": "icons/clouds.png",
            "Rain": "icons/rain.png",
            "Snow": "icons/snow.png",
        }.get(weather_condition, "icons/default.png")

        if not os.path.exists(img_path):
            img_path = "icons/default.png"

        self.weather_image = PhotoImage(file=img_path)
        self.weather_image = self.weather_image.subsample(2, 2)
        self.weather_image_label.configure(image=self.weather_image)

        self.temp_label = customtkinter.CTkLabel(self, text=f"🌡️ {current_temperature}°C\n\n{disaster}", font=customtkinter.CTkFont(size=30, weight="bold"))
        self.temp_label.grid(row=1, column=2, columnspan=1, padx=(10, 10), pady=(10, 10), sticky="n")

        self.humidity_label = customtkinter.CTkLabel(self, text=f"Humidity: {humidity}%", font=customtkinter.CTkFont(size=16))
        self.humidity_label.grid(row=3, column=1, padx=(30, 0), pady=(10, 50), sticky="s")

        self.pressure_label = customtkinter.CTkLabel(self, text=f"Pressure: {pressure} hPa", font=customtkinter.CTkFont(size=16))
        self.pressure_label.grid(row=3, column=2, padx=(0, 0), pady=(10, 50), sticky="n")

        self.wind_speed_label = customtkinter.CTkLabel(self, text=f"Wind speed: {wind_speed} m/s", font=customtkinter.CTkFont(size=16))
        self.wind_speed_label.grid(row=3, column=3, padx=(0, 0), pady=(10, 50), sticky="ne")

        self.humidity_image_label = customtkinter.CTkLabel(self, text='', image=self.humidity_image)
        self.humidity_image_label.grid(row=2, column=1, rowspan=1, padx=(40, 0), pady=(0, 0), sticky="nsew")
        self.pressure_image_label = customtkinter.CTkLabel(self, text='', image=self.pressure_image)
        self.pressure_image_label.grid(row=2, column=2, rowspan=1, padx=(20, 20), pady=(0, 0), sticky="nsew")
        self.wind_speed_image_label = customtkinter.CTkLabel(self, text='', image=self.wind_speed_image)
        self.wind_speed_image_label.grid(row=2, column=3, rowspan=1, padx=(0, 0), pady=(0, 0), sticky="nsew")

        self.textbox_title.configure(text=f"{tempo_agr} • {global_place}")
        self.schedule_refresh()
        self.store_hist()
        self.show_widgets()

    # Remove everything except the sidebar
    def clear_screen(self):
        for widget in self.grid_slaves():
            if widget != self.sidebar_frame:
                widget.grid_forget()

    #clears screen and shows today weather, used to circulate between menus
    def back_to_today(self):
        self.clear_screen()
        self.store_search()

    #a button to go back to only the search bar, this part is kinda ugly there's probably a better way to do this but this works for now
    def back_to_search(self):
        for widget in self.grid_slaves():
            widget.grid_forget()
        self.geometry(f"{self.initial_width}x{self.initial_height}")
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(1, weight=1)
        self.empty_label = customtkinter.CTkLabel(self, text="")
        self.empty_label.grid(row=0, column=0, columnspan=3, padx=20, pady=(0, 0))
        self.title_label = customtkinter.CTkLabel(self, text="Choose a location", font=customtkinter.CTkFont(size=30, weight="bold"))
        self.title_label.grid(row=0, column=0, columnspan=3, padx=20, pady=(20,0))
        self.search_bar = customtkinter.CTkEntry(self, placeholder_text="Search...")
        self.search_bar.grid(row=1, column=1, padx=(20, 10), pady=(30, 0), sticky="ew")
        self.search_bar.bind("<Return>", self.store_search)  # Show widgets when Enter is pressed
        self.search_button = customtkinter.CTkButton(self, text="Search", command=self.store_search)
        self.search_button.grid(row=1, column=2, padx=(10, 20), pady=(30, 0))
        self.sidebar_frame = customtkinter.CTkFrame(self, width=140, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, rowspan=10, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(4, weight=1)
        self.logo_label = customtkinter.CTkLabel(self.sidebar_frame, text="Options", font=customtkinter.CTkFont(size=20, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))
        self.sidebar_button_1 = customtkinter.CTkButton(self.sidebar_frame, text="Today", command=self.back_to_today)
        self.sidebar_button_1.grid(row=1, column=0, padx=20, pady=10)
        self.sidebar_button_2 = customtkinter.CTkButton(self.sidebar_frame, text="Weekly", command=self.show_weekly_weather)
        self.sidebar_button_2.grid(row=2, column=0, padx=20, pady=10)
        self.sidebar_button_3 = customtkinter.CTkButton(self.sidebar_frame, text="History", command=self.show_weather_history)
        self.sidebar_button_3.grid(row=3, column=0, padx=20, pady=10)
        self.show_search_button = customtkinter.CTkButton(self.sidebar_frame, text="Change Recording", command=self.open_search_popup, width=12, height=1)
        self.show_search_button.grid(row=5, column=0, padx=20, pady=(0, 40), sticky="n")
        self.appearance_mode_label = customtkinter.CTkLabel(self.sidebar_frame, text="Appearance Mode:", anchor="w")
        self.appearance_mode_label.grid(row=7, column=0, padx=20, pady=(10, 0))
        self.appearance_mode_optionemenu = customtkinter.CTkOptionMenu(self.sidebar_frame, values=["Light", "Dark", "System"], command=self.change_appearance_mode_event)
        self.appearance_mode_optionemenu.grid(row=8, column=0, padx=20, pady=(10, 10))
        self.appearance_mode_optionemenu.set("Dark")
        self.sidebar_frame.grid_remove()
        self.weather_image_label = customtkinter.CTkLabel(self, text='')
        self.weather_image_label.grid(row=0, column=4, rowspan=4, padx=(10, 10), pady=(10, 0), sticky="nsew")
        self.history_label = customtkinter.CTkLabel(self.sidebar_frame, text=f"Recording: {hist_place}", font=customtkinter.CTkFont(size=12))
        self.history_label.grid(row=4, column=0, padx=20, pady=(0, 10), sticky="n")

    #clears screen and displays the forecast
    def show_weekly_weather(self):
        global_place = self.search_bar.get().title()
        self.clear_screen()
        forecast = get_weekly_forecast(global_place, API_KEY)

        if forecast is None:
            error_label = customtkinter.CTkLabel(self, text="City not found or API error", font=customtkinter.CTkFont(size=16, weight="bold"))
            error_label.grid(row=1, column=1, columnspan=3, padx=0, pady=(0,45))
            self.after(5000, error_label.destroy)  # Remove error message after 5 seconds
            return

        for day_index, day_data in enumerate(forecast):
            # Display forecast for each day
            date_time = datetime.strptime(day_data['date_time'], "%Y-%m-%d %H:%M:%S")
            # Format the date as "dd-mm"
            date = date_time.strftime("%d-%m")
            max_temperature = int(day_data['max_temperature'])
            min_temperature = int(day_data['min_temperature'])
            humidity = day_data['humidity']
            pressure = day_data['pressure']
            wind_speed = day_data['wind_speed']
            weather_condition = day_data['weather_condition']

            # Load the weather images
            img_path = {
                "Clear": "icons/clear.png",
                "Clouds": "icons/clouds.png",
                "Rain": "icons/rain.png",
                "Snow": "icons/snow.png",
            }.get(weather_condition, "icons/default.png")

            if not os.path.exists(img_path):
                img_path = "icons/default.png"

            weather_image = PhotoImage(file=img_path)
            weather_image = weather_image.subsample(3, 3)
            weather_image_label = customtkinter.CTkLabel(self, text='', image=weather_image)
            weather_image_label.grid(row=1, column=day_index*6+1, columnspan=3, padx=20, pady=(0,5))

            # Display forecast data for each day
            day_label = customtkinter.CTkLabel(self, text=f"{date}", font=customtkinter.CTkFont(size=24, weight="bold"))
            day_label.grid(row=0, column=day_index*6+1, columnspan=3, padx=20, pady=(30,0))

            max_temp_label = customtkinter.CTkLabel(self, text=f"Temperature: {min_temperature}-{max_temperature}°C", font=customtkinter.CTkFont(size=16))
            max_temp_label.grid(row=2, column=day_index*6+1, columnspan=3, padx=20, pady=(0,5))

            humidity_label = customtkinter.CTkLabel(self, text=f"Humidity: {humidity}%", font=customtkinter.CTkFont(size=16))
            humidity_label.grid(row=3, column=day_index*6+1, columnspan=3, padx=20, pady=(0,5))

            pressure_label = customtkinter.CTkLabel(self, text=f"Pressure: {pressure} hPa", font=customtkinter.CTkFont(size=16))
            pressure_label.grid(row=4, column=day_index*6+1, columnspan=3, padx=20, pady=(0,5))

            wind_speed_label = customtkinter.CTkLabel(self, text=f"Wind speed: {wind_speed} m/s", font=customtkinter.CTkFont(size=16))
            wind_speed_label.grid(row=5, column=day_index*6+1, columnspan=3, padx=20, pady=(0,10))


        self.geometry(f"{self.initial_width + 580}x{self.initial_height + 220}")

        #burron to create graph
        graph_button = customtkinter.CTkButton(self, text="Graph", command=self.show_weekly_graph)
        graph_button.grid(row=6, column=1, columnspan=2, padx=(20,0), pady=(10, 20))
        graph_button.configure(font=customtkinter.CTkFont(size=16))
        
        # Dropdown menu for selecting data to plot
        options = ["Temperature", "Humidity", "Pressure", "Wind Speed"]
        self.graph_option = tk.StringVar()
        self.graph_option.set(options[0])  # Set the default option
        graph_dropdown = ttk.Combobox(self, textvariable=self.graph_option, values=options, state="readonly", width=12, height=8)
        graph_dropdown.grid(row=6, column=3, padx=(20,0), pady=(10, 20))
        graph_dropdown.config(font=customtkinter.CTkFont(size=16))

        # Configure style for dropdown menu
        style = ttk.Style()
        style.theme_use('clam')  # Use a theme that supports styling
        style.configure("Graph.TCombobox", background="gray10", foreground="gray10", fieldbackground="gray10", bordercolor="gray10")
        graph_dropdown.configure(style="Graph.TCombobox")


    #creates graphs for various variables
    def show_weekly_graph(self):
        global_place = self.search_bar.get().title() 
        weekly_forecast_data = get_weekly_forecast(global_place, API_KEY)

        if weekly_forecast_data:
            dates = [forecast["date_time"].split()[0] for forecast in weekly_forecast_data]  # Extract date part only
            selected_option = self.graph_option.get()

            #sets maximums and minimums depending on the type of data
            if selected_option == "Temperature":
                data_to_plot = [forecast["max_temperature"] for forecast in weekly_forecast_data]
                y_label = "Temperature (°C)"
                min_y = min(data_to_plot) - 10
                max_y = max(data_to_plot) + 10
            elif selected_option == "Humidity":
                data_to_plot = [forecast["humidity"] for forecast in weekly_forecast_data]
                y_label = "Humidity (%)"
                min_y = min(data_to_plot) - 20
                max_y = max(data_to_plot) + 20
            elif selected_option == "Pressure":
                data_to_plot = [forecast["pressure"] for forecast in weekly_forecast_data]
                y_label = "Pressure (hPa)"
                min_y = min(data_to_plot) - 30
                max_y = max(data_to_plot) + 30
            elif selected_option == "Wind Speed":
                data_to_plot = [forecast["wind_speed"] for forecast in weekly_forecast_data]
                y_label = "Wind Speed (m/s)"
                min_y = 0
                max_y = max(data_to_plot) + 10
            else:
                messagebox.showerror("Error", "Invalid option selected.")
                return

            # Plot the graph
            plt.plot(dates, data_to_plot)
            plt.xlabel("Date")
            plt.ylabel(y_label)
            plt.title("Weekly Forecast")
            plt.xticks(rotation=45)

            # Set y-axis limits
            plt.ylim(min_y, max_y)

            plt.tight_layout()

            # Show the graph
            plt.show()
        else:
            messagebox.showerror("Error", "Failed to fetch weekly forecast data.")

    #revelas the rest of the app after  the search is done, also expands window
    def show_widgets(self, event=None):
        if self.search_bar.get():  # Check if the search bar has any input
            self.sidebar_frame.grid()
            self.textbox_title.grid()
            self.back_button.grid()
            self.search_bar.grid_forget()
            self.search_button.grid_forget()
            self.title_label.grid_forget()
            self.empty_label.grid_forget()
            # Expand window size
            self.geometry(f"{self.initial_width + 450}x{self.initial_height + 220}")

#request weather data
def get_weather_data(global_place, API_KEY):
    base_url = "http://api.openweathermap.org/data/2.5/weather"
    params = {
        'q': global_place,
        'appid': API_KEY,
        'units': 'metric'  # Use 'imperial' for Fahrenheit
    }
    response = requests.get(base_url, params=params)
    data = response.json()

    if response.status_code == 200:
        main_data = data['main']
        current_temperature = main_data['temp']
        humidity = main_data['humidity']
        pressure = main_data['pressure']
        wind_data = data['wind']
        wind_speed = wind_data['speed']
        weather_data = data['weather'][0]
        weather_condition = weather_data['main']

        return current_temperature, humidity, pressure, wind_speed, weather_condition
    else:
        return None, None, None, None, None
#request weather forecast data
def get_weekly_forecast(global_place, API_KEY):
    base_url = "http://api.openweathermap.org/data/2.5/forecast"
    params = {
        'q': global_place,
        'appid': API_KEY,
        'units': 'metric'  # Use 'imperial' for Fahrenheit
    }
    response = requests.get(base_url, params=params)
    data = response.json()

    if response.status_code == 200:
        forecast_data = data['list'][:40]  # Adjust the range to fetch forecast every 8 days (5 days * 8 intervals = 40)
        forecast = []
        for i in range(0, len(forecast_data), 8):  # Loop with step size of 8
            items = forecast_data[i:i+8]  # Get forecast data for 8 days interval
            max_temp = max(item['main']['temp_max'] for item in items)
            min_temp = min(item['main']['temp_min'] for item in items)
            item = items[0]  # Use the first item for other details (they should be same for all items in 8-day interval)
            forecast.append({
                'date_time': item['dt_txt'],
                'max_temperature': max_temp,
                'min_temperature': min_temp,
                'humidity': item['main']['humidity'],
                'pressure': item['main']['pressure'],
                'wind_speed': item['wind']['speed'],
                'weather_condition': item['weather'][0]['main']
            })
        return forecast
    else:
        return None

#self-explanatory :/
def average_five(values):
    soma = 0
    for i in range(0,5):
        soma+=values[i]
    average_five = soma/5
    return average_five 

#the algorithm to estimate disaster probability, probably not very accurate but it's what we have without machine learning
def predict_weather_event(forecast):
    floodprob = 0
    stormprob = 0
    tornadoprob = 0
    droughtprob = 0


    temps_max = [day["max_temperature"] for day in forecast]
    temps_min = [day["min_temperature"] for day in forecast]
    humidities = [day["humidity"] for day in forecast]
    pressures = [day["pressure"] for day in forecast]
    winds = [day["wind_speed"] for day in forecast]

    temps_max_avg = average_five(temps_max)
    temps_min_avg = average_five(temps_min)
    hum_avg = average_five(humidities)
    press_avg = average_five(pressures)
    winds_avg = average_five(winds)
    temp_variation = temps_max_avg - temps_min_avg
    humidity_variation = max(humidities) - min(humidities)

    if temps_max_avg > 30:
        droughtprob += 10
        excess_temp = temps_max_avg - 30
        droughtprob += excess_temp*2.5

    if hum_avg < 30:
        droughtprob += 10
        excess_hum = 30 - hum_avg
        droughtprob += excess_hum*1.5

    if press_avg < 990:
        stormprob += 20
        excess_press = 990 - press_avg
        stormprob += excess_press*2

    if winds_avg > 30:
        stormprob += 30
    elif winds_avg > 50:
        tornadoprob += 30
        stormprob += 30
        excess_wind = 30 - winds_avg
        tornadoprob += excess_wind*1.5
        stormprob += excess_wind*1.5

    if hum_avg > 65 and humidity_variation < 20:
        floodprob += 25
        excess_hum2 = hum_avg - 65
        floodprob += excess_hum2*1.3
    elif hum_avg > 55 and humidity_variation > 20:
        floodprob += 30
        excess_hum2 = hum_avg - 55
        excess_hum_var = 20 - humidity_variation
        floodprob += excess_hum2*2 + excess_hum_var*2

    probabilities = [int(floodprob), int(droughtprob), int(tornadoprob), int(stormprob)]
    chance = max(probabilities)
    
    if chance == probabilities[0]:
        disaster = "flood"
    elif chance == probabilities[1]:
        disaster = "drought"
    elif chance == probabilities[2]:
        disaster = "tornado"
    elif chance == probabilities[3]:
        disaster = "storm"

    if chance > 0:
        return f"{chance}% chance of {disaster}"
    else:
        return "No disaster in sight"

#checks if the sting received is a valid city recognized by the api
def check_city_validity(city_name, API_KEY):
    base_url = "http://api.openweathermap.org/data/2.5/weather"
    params = {
        'q': city_name,
        'appid': API_KEY,
    }
    response = requests.get(base_url, params=params)
    if response.status_code == 200:
        return True
    else:
        return False





def run_app():
    app = App()
    app.mainloop()


if __name__ == "__main__":
    app = App()
    app.mainloop()
