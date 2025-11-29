import os
import time
import math
import rasterio
import configparser
import customtkinter
import tkinter as tk

from tkinter import messagebox
from PIL import Image, ImageTk
from customtkinter import CTkEntry
from tkintermapview import TkinterMapView



# Markers List for save
markers = []
my_location_marker_list = []
selected_two_markers = []
path_line_values = []

# Глобальный массив для сохранения данных
path_elevation_data = []

# Флаг для отслеживания состояния окна
is_window_open = False



# Path to directory for elevation
directory = '/home/ids/Desktop/Tigran/compileTest/MapCompile/ElevationData/'
markers_ini_file = 'markers.ini'
my_lat, my_lon = 40.1830, 44.5162 # My coordinates
EARTH_RADIUS = 6371  # earth radius in km
selected_icon = 3 # number of selected icon
previous_left = 0 # last click time for using double click
dot_count = 0 # dot count in entry for current recording degree
angle_entry_get = 0 # global angle value in entry



lat_lon = None
label_icon_image = None
tiff_file = None # value to choose current tiff file
custom_icon = None # custom icon value if other icon not selected
icon_path = None # path to icon image
path_line = None #
selected_marker_id = None
selected_marker_lat = None
selected_marker_lon = None
first_coords = None


customtkinter.set_default_color_theme("green")



APP_NAME = "MAP IDS by TigRRR"
WIDTH = 1920
HEIGHT = 1080



# Define selection ranges for different zoom levels
selection_ranges = {
    9: 0.024,
    10: 0.013,
    11: 0.0085,
    12: 0.0045,  # Example range for current zoom
    13: 0.0025,
    14: 0.0015,
    15: 0.0008,
    16: 0.0005,
    # Add more ranges as needed
}



def get_selection_range(zoom_level):
    return selection_ranges.get(zoom_level, 0.0045)  # Default range



def load_markers_ini(text_color_def='#ff0000'):
    global selected_icon, icon_path
    config = configparser.ConfigParser()
    config.read('markers.ini')
    markers.clear()

    if 'Markers' in config.sections():
        for marker_id in config.options('Markers'):
            marker_data = config.get('Markers', marker_id).split(',')
            lat = float(marker_data[0])
            lon = float(marker_data[1])
            text_color = marker_data[2]
            icon_name = marker_data[3]

            # Загружаем иконку с указанным путем
            try:
                if icon_name == '1':
                    icon_path = '/home/ids/Desktop/Tigran/compileTest/MapCompile/TkinterMapView/examples/button_image1.png'
                elif icon_name == '2':
                    icon_path = '/home/ids/Desktop/Tigran/compileTest/MapCompile/TkinterMapView/examples/button_image2.png'
                elif icon_name == '3':
                    icon_path = '/home/ids/Desktop/Tigran/compileTest/MapCompile/TkinterMapView/examples/button_image3.png'

                if os.path.exists(icon_path):  # Проверяем, существует ли файл
                    icon_image = Image.open(icon_path)
                    icon_image_res = icon_image.resize((35, 35))  # Применяем нужный размер
                    icon = ImageTk.PhotoImage(icon_image_res)
                else:
                    raise FileNotFoundError(f"Иконка {icon_name} не найдена.")

            except Exception as e:
                # print(f"Ошибка загрузки иконки {icon_name}: {e}")
                messagebox.showerror(title='Icon Error', message='Error to use this icon, used default icon!!!')

                # Если не удалось загрузить иконку, используем дефолтную

                default_icon_path = "button_image3.png"  # Путь к дефолтной иконке
                icon_image = Image.open(default_icon_path)
                icon_image_res = icon_image.resize((35, 35))
                icon = ImageTk.PhotoImage(icon_image_res)

            # Восстанавливаем маркер на карте
            elevation = get_elevation_from_tif(lat, lon)
            marker_id = map_widget.set_marker(lat, lon, f"Lat: {round(lat, 4)}\nLon: {round(lon, 4)}\nH: {elevation}",
                                              icon=icon, text_color=text_color_def, font='Tahoma 11')

            markers.append((marker_id, lat, lon, text_color, icon_name))



def save_markers_ini():
    config = configparser.ConfigParser()

    # Очищаем старые маркеры
    config.remove_section('Markers')
    config.add_section('Markers')

    for marker_id, lat, lon, text_color, icon_name in markers:
        config.set('Markers', str(marker_id), f"{lat},{lon},{'#ff0000'},{icon_name}")

    with open('markers.ini', 'w') as configfile:
        config.write(configfile)



def know_selected_icon_on_lbl():
    global selected_icon, label_icon_image

    if selected_icon == 3:
        label_icon_image = customtkinter.CTkImage(light_image=Image.open("/home/ids/Desktop/Tigran/compileTest/MapCompile/TkinterMapView/examples/button_image3.png"),
                                                  dark_image=Image.open("/home/ids/Desktop/Tigran/compileTest/MapCompile/TkinterMapView/examples/button_image3.png"),
                                                  size=(scale(42, scale_width), scale(42, scale_width)))
        used_icon_lbl.configure(image=label_icon_image)
    if selected_icon == 2:
        label_icon_image = customtkinter.CTkImage(light_image=Image.open("/home/ids/Desktop/Tigran/compileTest/MapCompile/TkinterMapView/examples/button_image2.png"),
                                                  dark_image=Image.open("/home/ids/Desktop/Tigran/compileTest/MapCompile/TkinterMapView/examples/button_image2.png"),
                                                  size=(scale(42, scale_width), scale(42, scale_width)))
        used_icon_lbl.configure(image=label_icon_image)
    if selected_icon == 1:
        label_icon_image = customtkinter.CTkImage(light_image=Image.open("/home/ids/Desktop/Tigran/compileTest/MapCompile/TkinterMapView/examples/button_image1.png"),
                                                  dark_image=Image.open("/home/ids/Desktop/Tigran/compileTest/MapCompile/TkinterMapView/examples/button_image1.png"),
                                                  size=(scale(42, scale_width), scale(42, scale_width)))
        used_icon_lbl.configure(image=label_icon_image)



def on_set_marker_button_click():
    try:
        # Try to get the coordinates from the entries and convert them to floats
        lat = float(lat_entry.get())
        lon = float(lon_entry.get())
        if (-90 < lat < 90) and (-180 < lon < 180):
            # If the conversion is successful, call the function to set the marker
            set_marker_by_coordinates((lat, lon))
        else:
            messagebox.showerror(title='Invalid values', message='Non-existent coordinates!')
            lat_entry.delete(0, 'end')
            lon_entry.delete(0, 'end')

    except ValueError:
        # If the conversion fails (empty string or invalid number), show an error message
        messagebox.showerror(title='Invalid values', message="Please enter valid latitude and longitude.")



def set_marker_by_coordinates(coords):
    global selected_icon
    if map_widget.tile_server == 'https://mt0.google.com/vt/lyrs=m&hl=en&x={x}&y={y}&z={z}&s=Ga':
        lat, lon = coords
        elevation = get_elevation_from_tif(lat, lon)
        text_color = '#ff0000'

        marker_id = map_widget.set_marker(lat, lon, f"Lat: {round(lat, 4)}\nLon: {round(lon, 4)}\nH: {elevation}",
                                          icon=custom_icon, text_color=text_color, font='Tahoma 11')
        # print(f"Marker set at: lat={lat}, lon={lon}")

        lat_entry.delete(0, 'end')
        lon_entry.delete(0, 'end')

        markers.append((marker_id, lat, lon, text_color, selected_icon))  # Include icon here
        save_markers_ini()  # Сохраняем маркеры после добавления

    elif map_widget.tile_server == 'https://mt0.google.com/vt/lyrs=s&hl=en&x={x}&y={y}&z={z}&s=Ga':
        lat, lon = coords
        elevation = get_elevation_from_tif(lat, lon)
        text_color = '#ffffff'

        marker_id = map_widget.set_marker(lat, lon, f"Lat: {round(lat, 4)}\nLon: {round(lon, 4)}\nH: {elevation}",
                                          icon=custom_icon, text_color=text_color, font='Tahoma 11')
        # print(f"Marker set at: lat={lat}, lon={lon}")

        lat_entry.delete(0, 'end')
        lon_entry.delete(0, 'end')

        markers.append((marker_id, lat, lon, text_color, selected_icon))  # Include icon here
        save_markers_ini()  # Сохраняем маркеры после добавления



def open_new_window():
    global is_window_open
    if is_window_open:
        return
    new_width = 220
    new_height = 250
    # Открытие нового окна с тремя кнопками
    new_window = tk.Toplevel(root)  # Создаем новое окно (Toplevel)
    new_window.geometry(f'{new_width}x{new_height}')
    new_window.title("Choose Icon")
    is_window_open = True

    # Переменная для отслеживания текущей выбранной кнопки
    selected_button = tk.IntVar()


    # Обработчик закрытия окна
    def on_close():
        global is_window_open
        is_window_open = False  # Сбрасываем флаг при закрытии окна
        new_window.destroy()

    new_window.protocol("WM_DELETE_WINDOW", on_close)


    def on_button_click(button_id):
        global selected_icon, custom_icon
        # Обновляем переменную и изменяем состояние кнопок
        selected_button.set(button_id)
        update_button_state()
        selected_icon = button_id

        if selected_icon == 1:
            custom_icon = ImageTk.PhotoImage(resized_image1)
            know_selected_icon_on_lbl()
            # print(selected_icon)

        elif selected_icon == 2:
            custom_icon = ImageTk.PhotoImage(resized_image2)
            know_selected_icon_on_lbl()
            # print(selected_icon)

        elif selected_icon == 3:
            custom_icon = ImageTk.PhotoImage(resized_image3)
            know_selected_icon_on_lbl()
            # print(selected_icon)


    def update_button_state():
        for i in range(1, 4):
            button = button_list[i-1]
            if selected_button.get() == i:
                button.config(relief=tk.SUNKEN, image=images[i-1])
            else:
                button.config(relief=tk.RAISED, image=images_default[i-1])


    # Загружаем изображения для кнопок
    img1 = Image.open("/home/ids/Desktop/Tigran/compileTest/MapCompile/TkinterMapView/examples/button_image1.png")
    img2 = Image.open("/home/ids/Desktop/Tigran/compileTest/MapCompile/TkinterMapView/examples/button_image2.png")
    img3 = Image.open("/home/ids/Desktop/Tigran/compileTest/MapCompile/TkinterMapView/examples/button_image3.png")


    # Загружаем изображения для обычного состояния кнопок
    img1_default = ImageTk.PhotoImage(img1.resize((50, 50)))
    img2_default = ImageTk.PhotoImage(img2.resize((50, 50)))
    img3_default = ImageTk.PhotoImage(img3.resize((50, 50)))


    # Список изображений для кнопок
    images = [img1_default, img2_default, img3_default]
    images_default = [img1_default, img2_default, img3_default]


    # Создаем 3 кнопки с изображениями
    button_list = [
        tk.Button(new_window, width=60, height=60, command=lambda: on_button_click(1), image=img1_default),
        tk.Button(new_window, width=60, height=60, command=lambda: on_button_click(2), image=img2_default),
        tk.Button(new_window, width=60, height=60, command=lambda: on_button_click(3), image=img3_default),
    ]


    # Размещаем кнопки на окне
    for button in button_list:
        button.pack(padx=10, pady=10)

    # Изначально состояние кнопок
    update_button_state()



# Function to get elevation
def get_elevation_from_tif(lat, lon):
    global tiff_file  # Make sure to use the global variable

    try:
        # lat and lon to get correct tiff file
        lat_for_tiff = str(math.trunc(lat))
        lon_for_tiff = str(math.trunc(lon))

        # Get all tiff files from directory
        files_in_directory = os.listdir(directory)

        # Filter files to get correct
        filtered_files = [file for file in files_in_directory if lat_for_tiff in file and lon_for_tiff in file]

        # Get full path for all files
        full_path = [os.path.join(directory, file) for file in filtered_files]

        for path in full_path:
            global tiff_file
            tiff_file = path

        with rasterio.open(tiff_file) as src:
            # Convert lat/lon to row/column
            row, col = src.index(lon, lat)
            elevation = src.read(1)[row, col]
            return elevation

    except IndexError:
        # print("Coordinates are out of bounds.")
        messagebox.showinfo(title='Coordinates are out at database', message='Increase the data set for elevation in this coords!')
        return None

    except Exception as e:
        # print(f"Error: {e}")
        messagebox.showerror(message=f'Invalid coordinates {e}!')
        return None



# Add marker
def add_marker_event(coords):
    global selected_icon

    if map_widget.tile_server == 'https://mt0.google.com/vt/lyrs=m&hl=en&x={x}&y={y}&z={z}&s=Ga':
        # print("Add marker: ", coords)
        lat, lon = coords
        elevation = get_elevation_from_tif(lat, lon)
        text_color = '#ff0000'
        marker_id = map_widget.set_marker(lat, lon, text=f"Lat: {round(coords[0], 4)}\nLon: {round(coords[1], 4)}\nH: {elevation}",
                                          icon=custom_icon, text_color=text_color, font='Tahoma 11')
        markers.append((marker_id, lat, lon, text_color, selected_icon))
        save_markers_ini()  # Сохраняем маркеры после добавления


    elif map_widget.tile_server == 'https://mt0.google.com/vt/lyrs=s&hl=en&x={x}&y={y}&z={z}&s=Ga':
        # print("Add marker: ", coords)
        lat, lon = coords
        elevation = get_elevation_from_tif(lat, lon)
        text_color = '#ffffff'
        marker_id = map_widget.set_marker(lat, lon, text=f"Lat: {round(coords[0], 4)}\nLon: {round(coords[1], 4)}\nH: {elevation}",
                                          icon=custom_icon, text_color=text_color, font='Tahoma 11')
        markers.append((marker_id, lat, lon, text_color, selected_icon))
        save_markers_ini()  # Сохраняем маркеры после добавления



# Delete all markers
def delete_all_markers():
    global path_line
    user_choose_btn = messagebox.askokcancel(title='DELETE ALL MARKERS', message='Are you sure you want to remove all markers?')

    if user_choose_btn:

        if len(markers) > 0:
            del_markers = map_widget.delete_all_marker()
            label_right.configure(text='')
            markers.clear()
            if path_line is not None:
                del_path_marks()
            save_markers_ini()
            # print('All markers DELETED!')

        else:
            messagebox.showinfo(title='DELETE ALL MARKERS', message='There is not a single marker to delete!')



def add_marker_dbl_click(coords):
    global selected_icon

    if map_widget.tile_server == 'https://mt0.google.com/vt/lyrs=m&hl=en&x={x}&y={y}&z={z}&s=Ga':
        lat, lon = coords
        elevation = get_elevation_from_tif(lat, lon)
        text_color = '#ff0000'
        marker_id = map_widget.set_marker(lat, lon, f"Lat: {round(lat, 4)}\nLon: {round(lon, 4)}\nH: {elevation}",
                                          icon=custom_icon, text_color=text_color, font='Tahoma 11')
        markers.append((marker_id, lat, lon, text_color, selected_icon))  # Добавляем иконку
        save_markers_ini()  # Сохраняем маркеры после добавления


    elif map_widget.tile_server == 'https://mt0.google.com/vt/lyrs=s&hl=en&x={x}&y={y}&z={z}&s=Ga':
        lat, lon = coords
        elevation = get_elevation_from_tif(lat, lon)
        text_color = '#ffffff'
        marker_id = map_widget.set_marker(lat, lon, f"Lat: {round(lat, 4)}\nLon: {round(lon, 4)}\nH: {elevation}",
                                          icon=custom_icon, text_color=text_color, font='Tahoma 11')
        markers.append((marker_id, lat, lon, text_color, selected_icon))  # Добавляем иконку
        save_markers_ini()  # Сохраняем маркеры после добавления



def mouse_clicks(coords):
    global previous_left, selected_marker_id, selected_marker_lat, selected_marker_lon, selected_two_markers, lat_lon
    current_time = time.time()
    time_diff = current_time - previous_left

    if time_diff < 0.2:  # Check for double click
        # print('Double click detected.')
        add_marker_dbl_click(coords)

    else:
        current_zoom = map_widget.zoom
        selection_range = get_selection_range(current_zoom)

        for marker in markers:
            # Проверим сколько элементов в маркере
            if len(marker) == 5:
                marker_id, lat, lon, text_color, icon = marker
                lat_lon = lat, lon
                if abs(lat - coords[0]) < selection_range and abs(lon - coords[1]) < selection_range:
                    selected_marker_id = marker_id
                    if len(selected_two_markers) < 2:
                        selected_two_markers.append(lat_lon)
                    else:
                        selected_two_markers.remove(selected_two_markers[0])
                        selected_two_markers.append(lat_lon)
                    selected_marker_lat = lat
                    selected_marker_lon = lon
                    label_right.configure(text=f'Marker {round(lat, 4), round(lon, 4)} selected!')
                    # print(f"Marker selected: {lat, lon}")
                    return
                else:
                    selected_marker_id = None
                    label_right.configure(text='')

            elif len(marker) == 4:
                marker_id, lat, lon, text_color = marker
                lat_lon = lat, lon
                if abs(lat - coords[0]) < selection_range and abs(lon - coords[1]) < selection_range:
                    selected_marker_id = marker_id
                    if len(selected_two_markers) < 2:
                        selected_two_markers.append(lat_lon)
                    else:
                        selected_two_markers.remove(selected_two_markers[0])
                        selected_two_markers.append(lat_lon)
                    selected_marker_lat = lat
                    selected_marker_lon = lon
                    label_right.configure(text=f'Marker {round(lat, 4), round(lon, 4)} selected!')
                    # print(f"Marker selected: {lat, lon}")
                    icon = None  # Если иконки нет, установим по умолчанию
                    return
                else:
                    selected_marker_id = None
                    label_right.configure(text='')
            else:
                # print(f"Некорректный формат маркера: {marker}")
                continue

    previous_left = current_time



# Function to delete the selected marker
def delete_selected_marker():
    global selected_marker_id, selected_marker_lat, selected_marker_lon

    lat_lon = (selected_marker_lat, selected_marker_lon)

    if selected_marker_id is not None:
        marker_id = selected_marker_id
        marker_id.delete()

        markers[:] = [m for m in markers if m[0] != selected_marker_id] # Remove the deleted marker
        selected_two_markers[:] = [m for m in selected_two_markers if m[0] != selected_marker_id]
        # print(f'Marker {selected_marker_id} deleted!')

        if lat_lon in selected_two_markers:
            for mark in selected_two_markers:
                if mark == lat_lon:
                    selected_two_markers.remove(lat_lon)
                    for marker_path in path_line_values:
                        if marker_path == lat_lon:
                            del_path_marks()


        label_right.configure(text='')
        selected_marker_id = None
        selected_marker_lat = None
        selected_marker_lon = None
        save_markers_ini()

    else:
        # print('No marker selected to delete.')
        messagebox.showerror(title='ERROR', message='No marker selected!')



# Функция для вычисления расстояния между двумя точками
def haversine():
    global my_lat, my_lon, selected_marker_lat, selected_marker_lon, EARTH_RADIUS

    # Координаты двух маркеров
    lat1, lon1 = my_lat, my_lon
    lat2, lon2 = selected_marker_lat, selected_marker_lon

    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)

    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = math.sin(delta_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    distance_value_entry_get.configure(state='normal')
    distance_value_entry_get.delete(0, 'end')
    distance_value_entry_get.insert(0, f'{round(EARTH_RADIUS * c * 1000, 2)} m')

    # print(f"Расстояние между маркерами: {EARTH_RADIUS * c * 1000:.2f} км")

    return EARTH_RADIUS * c * 1000



# Функция для вычисления угла линии относительно севера
def calculate_bearing(lat1, lon1, lat2, lon2):
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)

    delta_lambda = math.radians(lon2 - lon1)

    x = math.sin(delta_lambda) * math.cos(phi2)
    y = math.cos(phi1) * math.sin(phi2) - math.sin(phi1) * math.cos(phi2) * math.cos(delta_lambda)

    bearing = math.degrees(math.atan2(x, y))  # Переводим угол в градусы

    # Приводим угол к диапазону от 0 до 360 градусов
    bearing = (bearing + 360) % 360

    return bearing



def connect_me_and_marker():
    global path_line, my_lat, my_lon, selected_marker_lat, selected_marker_lon, my_location_marker_list

    if len(my_location_marker_list) > 0:

        if (selected_marker_lat is not None) and (selected_marker_lon is not None) and (path_line is None):
            # Координаты двух маркеров
            lat1, lon1 = my_lat, my_lon
            lat2, lon2 = selected_marker_lat, selected_marker_lon

            # Рисуем линию между маркерами
            path_line = map_widget.set_path([(lat1, lon1), (lat2, lon2)], color="blue", width=2)

            path_line_values.append((lat1, lon1))
            path_line_values.append((lat2, lon2))

            # Вычисление расстояния
            total_distance = haversine()

            # Очистка массива перед началом новой операции
            path_elevation_data.clear()

            # Разбиваем путь на сегменты по 100 метров
            num_segments = int(total_distance // 100)

            for i in range(1, num_segments + 1):
                # Вычисляем пропорцию текущей точки
                fraction = (i * 100) / total_distance

                # Интерполируем координаты текущей точки
                interp_lat = lat1 + fraction * (lat2 - lat1)
                interp_lon = lon1 + fraction * (lon2 - lon1)

                # Получаем высоту для текущей точки
                elevation = get_elevation_from_tif(interp_lat, interp_lon)


                # Добавляем данные в массив
                path_elevation_data.append({
                    "point_index": i,
                    "lat": interp_lat,
                    "lon": interp_lon,
                    "distance_from_start": i * 100,
                    "elevation": elevation
                })


            # # Вывод всех данных
            # print("Данные по высотам:")
            # for data in path_elevation_data:
            #     print(data)

            # Вычисление угла относительно севера
            bearing = calculate_bearing(lat1, lon1, lat2, lon2)
            bearing_value_entry_get.configure(state='normal')
            bearing_value_entry_get.delete(0, 'end')
            bearing_value_entry_get.insert(0, f'{round(bearing, 2)}°')
            # print(f"Угол линии относительно севера: {bearing:.2f} градусов")

        elif (selected_marker_lat is not None) and (selected_marker_lon is not None) and (path_line is not None):
            messagebox.showerror(title='PATH', message='Path already exists, delete existing one to add another!')

        else:
            messagebox.showerror(title='MARKER NOT SELECTED', message='Please select marker to draw path!')

    else:
        messagebox.showerror(title='MY LOCATION', message='Please add your location marker!')



# Функция для вычисления расстояния между двумя точками
def haversine_for_two_markers(lat1, lon1, lat2, lon2):

    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)

    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = math.sin(delta_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    distance_value_entry_get.configure(state='normal')
    distance_value_entry_get.delete(0, 'end')
    distance_value_entry_get.insert(0, f'{round(EARTH_RADIUS * c * 1000, 2)} m')

    # print(f"Расстояние между маркерами: {EARTH_RADIUS * c * 1000:.2f} км")

    return EARTH_RADIUS * c * 1000



def connect_two_markers():
    global path_line, my_location_marker_list, selected_two_markers

    if len(selected_two_markers) == 2:

        if path_line is None:
            # Координаты двух маркеров
            lat1, lon1 = selected_two_markers[0][0], selected_two_markers[0][1]
            lat2, lon2 = selected_two_markers[1][0], selected_two_markers[1][1]

            # Рисуем линию между маркерами
            path_line = map_widget.set_path([(lat1, lon1), (lat2, lon2)], color="blue", width=2)

            path_line_values.append((lat1, lon1))
            path_line_values.append((lat2, lon2))


            # Вычисление расстояния
            total_distance = haversine_for_two_markers(lat1, lon1, lat2, lon2)

            # Разбиваем путь на сегменты по 100 метров
            num_segments = int(total_distance // 100)
            elevations = []

            for i in range(1, num_segments + 1):
                # Вычисляем пропорцию текущей точки
                fraction = (i * 100) / total_distance

                # Интерполируем координаты текущей точки
                interp_lat = lat1 + fraction * (lat2 - lat1)
                interp_lon = lon1 + fraction * (lon2 - lon1)

                # Получаем высоту для текущей точки
                elevation = get_elevation_from_tif(interp_lat, interp_lon)
                elevations.append((interp_lat, interp_lon, elevation))

            # # Вывод всех точек с высотами
            # print("Высоты по пути:")
            # for idx, (lat, lon, elevation) in enumerate(elevations, start=1):
            #     print(f"{idx}: Координаты: ({lat:.4f}, {lon:.4f}), Высота: {elevation} м")

            # Вычисление угла относительно севера
            bearing = calculate_bearing(lat1, lon1, lat2, lon2)
            bearing_value_entry_get.configure(state='normal')
            bearing_value_entry_get.delete(0, 'end')
            bearing_value_entry_get.insert(0, f'{round(bearing, 2)}°')

            # print(f"Угол линии относительно севера: {bearing:.2f} градусов")

        elif path_line is not None:
            messagebox.showerror(title='PATH', message='Path already exists, delete existing one to add another!')

    elif len(selected_two_markers) == 1:
        messagebox.showerror(title='MARKERS NOT SELECTED', message='Please select one more marker to draw path!')

    else:
        messagebox.showerror(title='MARKERS NOT SELECTED', message='Please select markers to draw path!')



def del_path_marks():
    global path_line, path_line_values

    if path_line is not None:
        map_widget.delete(path_line)
        bearing_value_entry_get.delete(0, 'end')
        distance_value_entry_get.delete(0, 'end')
        path_line = None
        path_line_values = []

    else:
        messagebox.showwarning(title='PATH', message="You can't delete the path, because it doesn't exist!")



def my_location_marker():
    global my_lat, my_lon

    if len(my_location_marker_list) == 0:
        lat, lon = my_lat, my_lon
        text_color = '#ff0000'
        elevation = get_elevation_from_tif(lat, lon)
        marker_id = map_widget.set_marker(lat, lon, f"Lat: {round(lat, 4)}\nLon: {round(lon, 4)}\nH: {elevation}",
                                          icon=my_location_icon, text_color=text_color, font='Tahoma 11')
        my_location_marker_list.append(marker_id)

    else:
        messagebox.showinfo(title='MY LOCATION', message='You already have a marker showing your location!')



# Функция для валидации ввода
def validate_input(action, value):

    if action == '1':  # Если что-то добавляется

        try:
            # Проверяем, что значение состоит только из цифр или одной точки
            if value.count('.') > 1:  # Запрещаем больше одной точки
                return False

            # Удаляем точки и проверяем, что кроме них только цифры
            if not value.replace('.', '').isdigit():
                return False

            # Проверяем, что значение <= 360
            if float(value) > 360:
                return False

            # Запрещаем добавление точки, если значение уже равно 360
            if float(value) == 360 and '.' in value:
                return False

        except ValueError:
            return False

    # print(value)
    return True  # Разрешаем все другие действия (например, удаление)



# Функция для валидации ввода
def validate_input_lat(action, value):
    if action == '1':  # Если что-то добавляется
        try:
            # Разрешаем минус только в начале строки
            if value.startswith('-'):
                # print(f"Минус обнаружен: {value}")  # Для отладки
                value = value[1:]  # Убираем минус для дальнейшей проверки

                # Если после минуса идет ноль, то следующая цифра должна быть точка
                if len(value) > 0 and value[0] == '0' and len(value) > 1 and value[1] != '.':
                    # print("Ошибка после минуса: должна быть точка или другая цифра")  # Для отладки
                    return False
            else:
                # Если строка начинается с нуля, то следующая цифра должна быть точка
                if len(value) > 0 and value[0] == '0' and len(value) > 1 and value[1] != '.':
                    # print("Ошибка после нуля: должна быть точка или другая цифра")  # Для отладки
                    return False

            # Если строка пустая после удаления минуса (или вообще пустая, но минус был), разрешаем
            if value == '':
                # print('Строка пуста, но минус был введён. Разрешаем ввод.')  # Для отладки
                return True  # Минус пока допустим, ждем следующих символов

            # Проверяем количество точек
            if value.count('.') > 1:  # Запрещаем больше одной точки
                # print("Ошибка: слишком много точек")  # Для отладки
                return False

            # Проверяем, что строка состоит только из цифр или одной точки
            if not value.replace('.', '').isdigit():
                # print(f"Ошибка: неправильные символы в строке: {value}")  # Для отладки
                return False

            # Проверяем, что значение в пределах допустимых границ
            float_value = float(value)  # Преобразуем в число
            if float_value < -90:
                # print(f"Ошибка: значение меньше -90: {float_value}")  # Для отладки
                return False
            if float_value > 90:
                # print(f"Ошибка: значение больше 90: {float_value}")  # Для отладки
                return False

            # Запрещаем добавление точки, если значение уже равно 90 или -90
            if float_value == 90 and '.' in value:
                # print("Ошибка: точка при значении 90")  # Для отладки
                return False
            if float_value == -90 and '.' in value:
                # print("Ошибка: точка при значении -90")  # Для отладки
                return False

        except ValueError:
            # print("ValueError")  # Для отладки
            return False

    return True  # Разрешаем все другие действия (например, удаление)



def validate_input_lon(action, value):
    if action == '1':  # Если что-то добавляется
        try:
            # Разрешаем минус только в начале строки
            if value.startswith('-'):
                value = value[1:]  # Убираем минус для дальнейшей проверки

                # Если после минуса идет ноль, то следующая цифра должна быть точка
                if len(value) > 0 and value[0] == '0' and len(value) > 1 and value[1] != '.':
                    return False
            else:
                # Если строка начинается с нуля, то следующая цифра должна быть точка
                if len(value) > 0 and value[0] == '0' and len(value) > 1 and value[1] != '.':
                    return False

            # Если строка пустая после удаления минуса (или вообще пустая, но минус был), разрешаем
            if value == '':
                return True  # Минус пока допустим, ждем следующих символов

            # Проверяем количество точек
            if value.count('.') > 1:  # Запрещаем больше одной точки
                return False

            # Проверяем, что строка состоит только из цифр или одной точки
            if not value.replace('.', '').isdigit():
                return False

            # Проверяем, что значение в пределах допустимых границ
            float_value = float(value)  # Преобразуем в число
            if float_value < -180:
                return False
            if float_value > 180:
                return False

            # Запрещаем добавление точки, если значение уже равно 90 или -90
            if float_value == 180 and '.' in value:
                return False
            if float_value == -180 and '.' in value:
                return False

        except ValueError:
            return False

    return True  # Разрешаем все другие действия (например, удаление)



# Функция для валидации ввода
def validate_input_distance(action, value):

    if action == '1':  # Если что-то добавляется
        return value.isdigit()  # Разрешаем только цифры
    return True  # Разрешаем все другие действия (например, удаление)



def add_marker_by_angle_distance():
    global my_lat, my_lon, selected_icon, EARTH_RADIUS

    t_angle_deg = angle_entry.get()
    t_distance_m = distance_entry.get()

    if str(t_angle_deg) != '' or str(t_distance_m) != '':

        base_lat, base_lon = my_lat, my_lon
        angle_deg = float(angle_entry.get())
        distance_m = float(distance_entry.get())


        # Перевод угла в радианы
        angle_rad = math.radians(angle_deg)

        # Вычисление новых координат
        new_lat = base_lat + (distance_m / EARTH_RADIUS / 1000) * math.degrees(math.cos(angle_rad))
        new_lon = base_lon + (distance_m / EARTH_RADIUS / 1000) * math.degrees(math.sin(angle_rad) / math.cos(math.radians(base_lat)))


        if map_widget.tile_server == 'https://mt0.google.com/vt/lyrs=m&hl=en&x={x}&y={y}&z={z}&s=Ga':
            text_color = '#ff0000'
            elevation = get_elevation_from_tif(new_lat, new_lon)
            marker_id = map_widget.set_marker(new_lat, new_lon,
                                              f"Lat: {round(new_lat, 4)}\nLon: {round(new_lon, 4)}\nH: {elevation}",
                                              icon=custom_icon, text_color=text_color, font='Tahoma 11')

            angle_entry.delete(0, 'end')
            distance_entry.delete(0, 'end')

            markers.append((marker_id, new_lat, new_lon, text_color, selected_icon))  # Добавляем иконку
            save_markers_ini()  # Сохраняем маркеры после добавления


        elif map_widget.tile_server == 'https://mt0.google.com/vt/lyrs=s&hl=en&x={x}&y={y}&z={z}&s=Ga':
            text_color = '#ffffff'
            elevation = get_elevation_from_tif(new_lat, new_lon)
            marker_id = map_widget.set_marker(new_lat, new_lon,
                                              f"Lat: {round(new_lat, 4)}\nLon: {round(new_lon, 4)}\nH: {elevation}",
                                              icon=custom_icon, text_color=text_color, font='Tahoma 11')

            angle_entry.delete(0, 'end')
            distance_entry.delete(0, 'end')

            markers.append((marker_id, new_lat, new_lon, text_color, selected_icon))  # Добавляем иконку
            save_markers_ini()  # Сохраняем маркеры после добавления

    else:
        messagebox.showwarning(title='Invalid inputs', message='Please enter valid latitude and longitude values!')



def on_closing():
    save_markers_ini()
    root.destroy()



def on_closing_for_btn():
    message_input = messagebox.askokcancel(title='EXIT', message="Are you sure you want to close the programm?")

    if message_input == True:
        save_markers_ini()
        root.destroy()



def change_map(new_map: str):
    if new_map == "Google normal":
        map_widget.set_tile_server("https://mt0.google.com/vt/lyrs=m&hl=en&x={x}&y={y}&z={z}&s=Ga", max_zoom=12)
        new_color = '#ff0000'  # Red for normal

        for index, (marker_id, lat, lon, text_color, icon) in enumerate(markers):
            # Remove the existing marker
            marker_id.delete()

        load_markers_ini()


    elif new_map == "Google satellite":
        map_widget.set_tile_server("https://mt0.google.com/vt/lyrs=s&hl=en&x={x}&y={y}&z={z}&s=Ga", max_zoom=12)
        new_color = '#ffffff'  # White for satellite

        for index, (marker_id, lat, lon, text_color, icon) in enumerate(markers):
            # Remove the existing marker
            marker_id.delete()

        load_markers_ini(text_color_def=new_color)



# Функция для масштабирования размеров
def scale(value, scale_factor):
    return int(value * scale_factor)



# Create the main window
root = customtkinter.CTk()
root.title(APP_NAME)
root.geometry(f"{WIDTH}x{HEIGHT}")
root.resizable(False, False)



screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()

root.geometry(f"{screen_width}x{screen_height}")



if screen_width == 1920 and screen_height == 1080:
    # Вычисление коэффициентов масштабирования
    scale_width = screen_width / WIDTH
    scale_height = screen_height / HEIGHT
elif screen_width == 1600 and screen_height == 900:
    # Вычисление коэффициентов масштабирования
    scale_width = screen_width / WIDTH
    scale_height = screen_height / HEIGHT * 0.99
elif screen_width == 1280 and screen_height == 720:
    # Вычисление коэффициентов масштабирования
    scale_width = screen_width / WIDTH
    scale_height = screen_height / HEIGHT * 0.97



# Load and resize your custom icons
original_image1 = Image.open('/home/ids/Desktop/Tigran/compileTest/MapCompile/TkinterMapView/examples/button_image1.png')
resized_image1 = original_image1.resize((35, 35))  # Resize to 35x35 pixels


original_image2 = Image.open('/home/ids/Desktop/Tigran/compileTest/MapCompile/TkinterMapView/examples/button_image2.png')
resized_image2 = original_image2.resize((35, 35))  # Resize to 35x35 pixels


original_image3 = Image.open('/home/ids/Desktop/Tigran/compileTest/MapCompile/TkinterMapView/examples/button_image3.png')
resized_image3 = original_image3.resize((35, 35))  # ...


custom_icon = ImageTk.PhotoImage(resized_image3)



original_my_location_icon = Image.open('/home/ids/Desktop/Tigran/compileTest/MapCompile/TkinterMapView/examples/button_icon.png')
resized_my_loc_icon = original_my_location_icon.resize((35, 35))
my_location_icon = ImageTk.PhotoImage(resized_my_loc_icon)



# Setup database path
script_directory = os.path.dirname(os.path.abspath(__file__))
database_path = os.path.join(script_directory, "offline_tiles.db")



root.protocol("WM_DELETE_WINDOW", on_closing)
root.createcommand('tk::mac::Quit', on_closing)



left_frame_width = 300
right_frame_width = 1920 - left_frame_width
bottom_frame_height = 300
right_frame_height = 1015 - bottom_frame_height



# Ширина и высота фреймов
left_frame_width_scale = scale(300, scale_width)
right_frame_width_scale = scale(1920 - left_frame_width, scale_width)
bottom_frame_height_scale = scale(300, scale_height)
right_frame_height_scale = scale(1015 - bottom_frame_height, scale_height)



# Создание левого фрейма
frame_left = customtkinter.CTkFrame(master=root, width=right_frame_width_scale, height=scale(1015, scale_height), corner_radius=0)
frame_left.place(x=0, y=0)



# Создание правого фрейма
frame_right = customtkinter.CTkFrame(master=root, width=left_frame_width_scale, height=scale(right_frame_height + 300, scale_height), corner_radius=0)
frame_right.place(x=right_frame_width_scale, y=0)



# Создание панели с вкладками для правого фрейма
tabview = customtkinter.CTkTabview(master=frame_right, width=left_frame_width_scale, height=right_frame_height_scale, corner_radius=10)
tabview.place(x=0, y=0)



tabview.add('Main Panel')
tabview.add('Settings')
tabview.set('Main Panel')



# Создание нижнего фрейма
frame_bottom = customtkinter.CTkFrame(master=root, width=scale(right_frame_width + 300, scale_width), height=bottom_frame_height_scale, corner_radius=0, border_width=1)
frame_bottom.place(x=0, y=right_frame_height_scale)



frame_for_values = customtkinter.CTkFrame(master=frame_bottom, width=scale(600, scale_width), height=scale(170, scale_height), corner_radius=0, border_width=2, border_color='white')
frame_for_values.place(x=scale(15, scale_width), y=scale(15, scale_height))



frame_for_values_second = customtkinter.CTkFrame(master=frame_bottom, width=scale(600, scale_width), height=scale(170, scale_height), corner_radius=0, border_width=2, border_color='white')
frame_for_values_second.place(x=scale(635, scale_width), y=scale(15, scale_height))



frame_for_values_third = customtkinter.CTkFrame(master=frame_bottom, width=scale(600, scale_width), height=scale(270, scale_height), corner_radius=0, border_width=2, border_color='white')
frame_for_values_third.place(x=scale(1255, scale_width), y=scale(15, scale_height))



# Правый фрейм: кнопки и элементы
button_width = scale(260, scale_width)
button_height = scale(30, scale_height)
entry_width = scale(260, scale_width)
entry_height = scale(30, scale_height)
padding_x = scale(15, scale_width)
padding_y = scale(20, scale_height)
label_icon_image = customtkinter.CTkImage(
    light_image=Image.open("/home/ids/Desktop/Tigran/compileTest/MapCompile/TkinterMapView/examples/button_image3.png"),
    dark_image=Image.open("/home/ids/Desktop/Tigran/compileTest/MapCompile/TkinterMapView/examples/button_image3.png"),
    size=(scale(42, scale_width), scale(42, scale_width)))




del_markers_btn = customtkinter.CTkButton(master=tabview.tab('Main Panel'), text='Del All Markers', command=delete_all_markers, width=button_width, height=button_height)
del_markers_btn.place(x=padding_x, y=scale(padding_y + 600, scale_height))



bottom_button = customtkinter.CTkButton(master=tabview.tab('Main Panel'), text="My Location", command=my_location_marker, width=button_width, height=button_height)
bottom_button.place(x=padding_x, y=padding_y)



del_selected_marker_btn = customtkinter.CTkButton(master=tabview.tab('Main Panel'), text='Del Selected Marker', command=delete_selected_marker, width=button_width, height=button_height)
del_selected_marker_btn.place(x=padding_x, y=scale(padding_y + 60, scale_height))



icon_choose_btn = customtkinter.CTkButton(master=tabview.tab('Main Panel'), text='Choose Icon', command=open_new_window, width=button_width, height=button_height)
icon_choose_btn.place(x=padding_x, y=scale(padding_y + 540, scale_height))



map_label = customtkinter.CTkLabel(master=tabview.tab('Settings'), text="Tile Server:", anchor="w", width=button_width, height=scale(30, scale_height))
map_label.place(x=padding_x, y=padding_y)



map_option_menu = customtkinter.CTkOptionMenu(master=tabview.tab('Settings'), values=["Google normal", "Google satellite"], command=change_map, width=button_width, height=scale(30, scale_height))
map_option_menu.place(x=padding_x, y=scale(padding_y + 40, scale_height))



btn_root_close = customtkinter.CTkButton(master=tabview.tab('Settings'), text='Exit', command=on_closing_for_btn, width=button_width, height=button_height)
btn_root_close.place(x=padding_x, y=scale(padding_y + 600, scale_height))



# Левый фрейм: карта и заголовок
map_widget = TkinterMapView(frame_left, corner_radius=0, use_database_only=True, database_path=database_path, max_zoom=12)
map_widget.place(x=0, y=scale(30, scale_height), width=right_frame_width_scale, height=scale(right_frame_height - 30, scale_height))



label_right = customtkinter.CTkLabel(master=frame_left, text='', width=right_frame_width_scale, height=scale(20, scale_height))
label_right.place(x=scale(10, scale_width), y=scale(5, scale_height))



# Настройка валидации
vcmd = frame_bottom.register(validate_input)
vcmd_distance = frame_bottom.register(validate_input_distance)
vcmd_lat = frame_bottom.register(validate_input_lat)
vcmd_lon = frame_bottom.register(validate_input_lon)



angle_enter_label = customtkinter.CTkLabel(frame_for_values, text="Enter Bearing:", anchor="w", width=button_width, height=scale(30, scale_height))
angle_enter_label.place(x=scale(25, scale_width), y=scale(5, scale_height))



angle_entry = customtkinter.CTkEntry(frame_for_values, validate="key", validatecommand=(vcmd, '%d', '%P'), width=entry_width, height=entry_height, fg_color='#535353')
angle_entry.place(x=scale(25, scale_width), y=scale(45, scale_height))



distance_enter_label = customtkinter.CTkLabel(frame_for_values, text="Enter Distance:", anchor="w", width=button_width, height=scale(30, scale_height))
distance_enter_label.place(x=scale(25, scale_width), y=scale(85, scale_height))



distance_entry = customtkinter.CTkEntry(frame_for_values, validate="key", validatecommand=(vcmd_distance, '%d', '%P'), width=entry_width, height=entry_height, fg_color='#535353')
distance_entry.place(x=scale(25, scale_width), y=scale(125, scale_height))



btn_set_by_angle_dis = customtkinter.CTkButton(frame_bottom, text='Set Marker With Inputs', command=add_marker_by_angle_distance, width=button_width, height=button_height)
btn_set_by_angle_dis.place(x=scale(40, scale_width), y=scale(200, scale_height))



draw_path_to_sel_marker_btn = customtkinter.CTkButton(frame_bottom, text='Delete Path', command=del_path_marks, width=button_width, height=button_height)
draw_path_to_sel_marker_btn.place(x=scale(40, scale_width), y=scale(255, scale_height))



draw_path_to_sel_marker_btn = customtkinter.CTkButton(frame_bottom, text='Draw Path To Marker', command=connect_me_and_marker, width=button_width, height=button_height)
draw_path_to_sel_marker_btn.place(x=scale(330, scale_width), y=scale(200, scale_height))



get_bearing_label = customtkinter.CTkLabel(frame_for_values, text="Get Bearing:", anchor="w", width=button_width, height=scale(30, scale_height))
get_bearing_label.place(x=scale(315, scale_width), y=scale(5, scale_height))



bearing_value_entry_get = CTkEntry(frame_for_values, placeholder_text='Get bearing', width=entry_width, height=entry_height, state='readonly', fg_color='#535353')
bearing_value_entry_get.place(x=scale(315, scale_width), y=scale(45, scale_height))



get_distance_label = customtkinter.CTkLabel(frame_for_values, text="Get Distance:", anchor="w", width=button_width, height=scale(30, scale_height))
get_distance_label.place(x=scale(315, scale_width), y=scale(85, scale_height))



distance_value_entry_get = CTkEntry(frame_for_values, placeholder_text='Get Distance', width=entry_width, height=entry_height, state='readonly', fg_color='#535353')
distance_value_entry_get.place(x=scale(315, scale_width), y=scale(125, scale_height))



connect_two_markers_btn = customtkinter.CTkButton(frame_bottom, text='Connect Two Markers', command=connect_two_markers, width=button_width, height=button_height)
connect_two_markers_btn.place(x=scale(330, scale_width), y=scale(255, scale_height))



latitude_enter_label = customtkinter.CTkLabel(frame_for_values_second, text="Enter Latitude:", anchor="w", width=button_width, height=scale(30, scale_height))
latitude_enter_label.place(x=scale(25, scale_width), y=scale(5, scale_height))



lat_entry = customtkinter.CTkEntry(frame_for_values_second, validate="key", validatecommand=(vcmd_lat, '%d', '%P'), width=entry_width, height=entry_height, fg_color='#535353')
lat_entry.place(x=scale(25, scale_width), y=scale(45, scale_height))



longitude_enter_label = customtkinter.CTkLabel(frame_for_values_second, text="Enter Longitude:", anchor="w", width=button_width, height=scale(30, scale_height))
longitude_enter_label.place(x=scale(25, scale_width), y=scale(85, scale_height))



lon_entry = customtkinter.CTkEntry(frame_for_values_second, validate="key", validatecommand=(vcmd_lon, '%d', '%P'), width=entry_width, height=entry_height, fg_color='#535353')
lon_entry.place(x=scale(25, scale_width), y=scale(125, scale_height))



get_coords_btn = customtkinter.CTkButton(master=frame_bottom, text='Set Marker', command=on_set_marker_button_click, width=button_width, height=button_height)
get_coords_btn.place(x=scale(660, scale_width), y=scale(200, scale_height))



now_dont_know_what_btn = customtkinter.CTkButton(frame_bottom, text='None', command=None, width=button_width, height=button_height, state='disabled')
now_dont_know_what_btn.place(x=scale(660, scale_width), y=scale(255, scale_height))



used_icon_lbl = customtkinter.CTkLabel(frame_bottom, text='', image=label_icon_image, width=scale(21, scale_width), height=scale(21, scale_height))
used_icon_lbl.place(x=scale(1865, scale_width), y=scale(15, scale_height))



connect_markers_btn = customtkinter.CTkButton(frame_bottom, text='None', command=None, width=scale(21, scale_width), height=scale(21, scale_height), state='disabled')
connect_markers_btn.place(x=scale(1865, scale_width), y=scale(78, scale_height))



now_dont_know_what_btn2 = customtkinter.CTkButton(frame_bottom, text='None', command=None, width=scale(21, scale_width), height=scale(21, scale_height), state='disabled')
now_dont_know_what_btn2.place(x=scale(1865, scale_width), y=scale(141, scale_height))



# Add double click event from left click
map_widget.add_left_click_map_command(mouse_clicks)



# Set default values for the map
map_widget.set_position(40.1772, 44.5034)
get_zoom = map_widget.set_zoom(10)
map_option_menu.set("Google normal")
map_widget.set_tile_server("https://mt0.google.com/vt/lyrs=m&hl=en&x={x}&y={y}&z={z}&s=Ga", max_zoom=12)



if __name__ == "__main__":
    load_markers_ini()
    root.mainloop()  # Start the Tkinter main loop