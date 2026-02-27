#awm = automated whatsapp messenger

import re
import os
import cv2
import time
import math
import zipfile
import pyperclip
import pyautogui
import subprocess
import numpy as np 
from datetime import datetime
import psutil
import platform

# ==========================================
# 1. PATHS & GLOBAL VARIABLES
# ==========================================
# Define file paths - provide the path to the templates and or other files that will be needed here 
# example: searchbox_template = "Users/Me/ScreenShots/abc123.png"
screenshot_path = "path/to/store/screenshots/at"
output_image_with_boxes = "path/to/store/marked/images/at"
output_image_with_boxes_and_grid = "path/to/store/marked/and/grid/applied/images/at"

# Highly recommmned to keep everything in a single folder with subfolders preferably to avoid mess
punctuation_to_remove = '"'

# ==========================================
# 2. CORE TEMPLATE MATCHING & CLICKING LOGIC
# ==========================================

# Takes a full-screen screenshot to see what is currently on your display.
def take_screenshot(screenshot_path):
    screenshot = pyautogui.screenshot()
    screenshot.save(screenshot_path)

# Compares your current screen (screenshot_path) against what you want to find (template_path).
# It draws a red box around the matched area and saves it to output_path.
def display_combined_templates_and_boxes(screenshot_path, template_path, output_path):
    image = cv2.imread(screenshot_path)
    template = cv2.imread(template_path, cv2.IMREAD_GRAYSCALE)
    
    if image is None or template is None:
        print("Error: Image or template could not be loaded")
        return
        
    template = template.astype(np.uint8)
    if template.shape[0] > image.shape[0] or template.shape[1] > image.shape[1]:
        print("Error: Template is larger than the image")
        return
        
    image_with_box = image.copy() 
    # Calls the matching math function below
    box, how_good = match_template(image_with_box, template, (0, 0, 255)) 
    cv2.imwrite(output_path, image_with_box)
    return box, how_good

# The actual OpenCV math that scans the pixels to find your target button/image.
def match_template(image, template, color):
    gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    result = cv2.matchTemplate(gray_image, template, cv2.TM_CCOEFF_NORMED)
    _, max_val, _, max_loc = cv2.minMaxLoc(result)
    
    h, w = template.shape[:2] 
    top_left = max_loc
    bottom_right = (top_left[0] + w, top_left[1] + h)
    cv2.rectangle(image, top_left, bottom_right, color, 2)
    
    return (top_left, bottom_right) , max_val

# Draws a crosshair/grid on the image to help visualize where the center is.
def draw_grid(image_path, output_path):
    image = cv2.imread(image_path)
    if image is None:
        print("Error: Image could not be loaded")
    h, w, _ = image.shape
    cv2.line(image, (w // 2, 0), (w // 2, h), (255, 255, 255), 1)  
    cv2.line(image, (0, h // 2), (w, h // 2), (255, 255, 255), 1)  
    cv2.imwrite(output_path, image)

# Calculates the exact center of the box found by the template matcher.
def get_grid_coordinates(box_coords):
    top_left, bottom_right = box_coords
    grid_x = top_left[0] // 2
    grid_y = top_left[1] // 2
    return grid_x, grid_y

# Uses PyAutoGUI to physically move your mouse and click the coordinates.
def tap_coords(button_coordinates):
    position = button_coordinates 
    pyautogui.click(position[0], position[1])

# THE MASTER FUNCTION: Ties screenshot, matching, calculation, and clicking together.
# Feed it an image path, and it will find it on screen and click it.
def search_and_get_tapped(path):
    time.sleep(0.5)
    take_screenshot(screenshot_path)
    collect, how_good = display_combined_templates_and_boxes(screenshot_path, path, output_image_with_boxes)
    draw_grid(output_image_with_boxes, output_image_with_boxes_and_grid)
    how_good = math.ceil(how_good)
    
    # If the match accuracy is higher than 85%, execute the click.
    if how_good > 0.85:
        coords = get_grid_coordinates(collect)
        tap_coords(coords)
    return how_good


# ==========================================
# 3. CROSS-PLATFORM OS MANAGEMENT (MAC & WIN)
# ==========================================
# NOTE: Both Windows and Mac functionalities are built into this unified script.

# Checks if WhatsApp is actively running on a Mac using AppleScript.
def is_whatsapp_running_on_mac():
    result = subprocess.run(['osascript', '-e', 'tell application "System Events" to (name of processes) contains "WhatsApp"'], capture_output=True, text=True)
    return result.stdout.strip() == 'true'

# Checks if WhatsApp is actively running on Windows using process iteration.
def is_whatsapp_running_on_windows():
    for process in psutil.process_iter(['name']):
        if process.info['name'] in ['WhatsApp.exe', 'WhatsApp']:
            return True
    return False

# Forces Mac to open WhatsApp and bring it to the absolute front of the screen.
def open_whatsapp_on_mac():
    if is_whatsapp_running_on_mac():
        subprocess.run(['osascript', '-e', 'tell application "WhatsApp" to activate'])
    else:
        subprocess.Popen(["/Applications/WhatsApp.localized/WhatsApp.app/Contents/MacOS/WhatsApp"])
        time.sleep(3)  
        subprocess.run(['osascript', '-e', 'tell application "System Events" to tell process "WhatsApp" to set frontmost to true'])

# CROSS-PLATFORM LAUNCHER: Detects your OS and runs the appropriate startup sequence.
def open_whatsapp_windows():
    current_os = platform.system()
    
    if current_os == "Darwin":  # 'Darwin' means Mac OS
        if is_whatsapp_running_on_mac():
            subprocess.run(['osascript', '-e', 'tell application "WhatsApp" to activate'])
        else:
            subprocess.Popen(["/Applications/WhatsApp.localized/WhatsApp.app/Contents/MacOS/WhatsApp"])
            time.sleep(3)
            subprocess.run(['osascript', '-e', 'tell application "System Events" to tell process "WhatsApp" to set frontmost to true'])
            
    elif current_os == "Windows": # Windows OS
        subprocess.run(['cmd', '/c', 'start whatsapp://'], shell=True)
        time.sleep(5 if not is_whatsapp_running_on_windows() else 1)


# ==========================================
# 4. CHAT PARSING & DATA EXTRACTION
# ==========================================

# Scans a raw WhatsApp .txt export and grabs only messages sent between start_time and end_time.
def parse_messages_within_time_range(chat_lines, start_time, end_time):
    message_pattern = re.compile(r'\[(.*?)\] (.*?): (.*)', re.DOTALL)
    new_messages = []
    current_message = []
    capture = False
    
    for line in chat_lines:
        match = message_pattern.match(line)
        if match:
            timestamp_str, sender, message = match.groups()
            timestamp = datetime.strptime(timestamp_str, '%d/%m/%y, %I:%M:%S %p')
            if start_time <= timestamp <= end_time:
                if current_message:
                    new_messages.append('\n'.join(current_message).strip())
                current_message = [message.strip()]
                capture = True
            else:
                capture = False
        else:
            if capture:
                current_message.append(line.strip())
                
    if current_message:
        new_messages.append('\n'.join(current_message).strip())
    return new_messages

# Looks through messages for a specific keyword/string and handles attached media text.
def filter_messages_with_string(file_path, output_file_path, search_string):
    filtered_messages = []
    most_recent_message = ''
    recm=0
    
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
    
    messages = content.split('|')
    
    for message in messages:
        if search_string in message:
            if '-PHOTO-' in message or '-VIDEO-' in message or 'video omitted' in message or 'photo omitted' in message :
                bracket_index = message.find('[')
                part1 = message[:bracket_index].strip()
                if part1:
                    most_recent_message = part1
                    recm += 1
            else:
                most_recent_message = message
                recm+=1
            
    filtered_messages.append(most_recent_message.strip())
    
    with open(output_file_path, 'w', encoding='utf-8') as file:
        for message in filtered_messages:
            file.write(message + '\n\n')

    return message, recm

# Unzips an exported chat, reads the .txt inside, and filters it by time and keyword.
def search_and_rescue(which_chat_to_rescue, ghanta, search_string):
    if not os.path.exists(extract_path):
        os.makedirs(extract_path)

    with zipfile.ZipFile(which_chat_to_rescue, 'r') as zip_ref:
        zip_ref.extractall(extract_path)

    chat_file_path = [os.path.join(extract_path, f) for f in os.listdir(extract_path) if f.endswith('.txt')][0]

    with open(chat_file_path, 'r', encoding='utf-8') as file:
        chat_lines = file.readlines()

    now = datetime.now()
    start_time = now.replace(hour=ghanta, minute=0, second=0, microsecond=0)  
    end_time = now.replace(hour=23, minute=59, second=59, microsecond=0)  

    new_messages = parse_messages_within_time_range(chat_lines, start_time, end_time)

    with open(output_file_path, 'w', encoding='utf-8') as file:
        for message in new_messages:
            file.write('|' + message + '|' + '\n\n')

    reminder, recm = filter_messages_with_string(output_file_path, fixed_output_file_path, search_string)
    return reminder, recm

# Cleans up names by removing unwanted punctuation.
def save_list_with_identifier(file_path, output_file_path, identifier, punctuation_to_remove):
    with open(file_path, 'r', encoding='utf-8') as file:
        lines = file.readlines()
    
    translation_table = str.maketrans('', '', punctuation_to_remove)
    names = []
    
    for line in lines:
        normalized_line = re.sub(r'\s+', ' ', line)
        if identifier in normalized_line:
            name = normalized_line.split(identifier)[-1].strip()
            name = name.translate(translation_table)
            names.append(name)
            
    with open(output_file_path, 'w', encoding='utf-8') as file:
        for name in names:
            file.write(name + '\n')

# Maps names from a text file to phone numbers using a provided dictionary.
def get_nums(file_path, output_file_path, name_dict):
    with open(file_path, 'r', encoding='utf-8') as file:
        names = [line.strip().upper() for line in file if line.strip()] 
    
    with open(output_file_path, 'w', encoding='utf-8') as output_file:
        for name in names:
            phone_number = name_dict.get(name, 'Name not found')
            output_file.write(f"{phone_number}\n") 

# ==========================================
# 5. AUTOMATED ACTIONS (KEYBOARD & MOUSE)
# ==========================================

# Simulates pressing Cmd+V (Mac paste) and hits Enter. 
# NOTE: For Windows use, you'd change 'command' to 'ctrl'.
def just_paste():
    pyautogui.hotkey('command')
    pyautogui.hotkey('command', 'v')
    time.sleep(0.4)
    pyautogui.press('enter')

# Hardcoded coordinate clicker (useful if you know exact screen pixels).
def tap_coordinates(x,y):
    group_area_position = (x,y) 
    pyautogui.click(group_area_position[0], group_area_position[1])
    time.sleep(1)

# Copies text to clipboard, finds a specific search box using an image template, and pastes.
def paste_things(whattho, message_to_be_sent): 
    pyperclip.copy(whattho)
    search_and_get_tapped(search_box_template_path) # Assumes search_box_template_path is defined
    just_paste()

# Loops through a list of phone numbers and triggers the paste sequence for each.
def process_numbers(file_path, message_to_be_sent):
    with open(file_path, 'r', encoding='utf-8') as file:
        numbers = [line.strip() for line in file if line.strip()]  
    
    for number in numbers:
        if number != 'Name not found':
            paste_things(number, message_to_be_sent)

# Prepares the interface (using hotkeys) and then starts processing the list of numbers.
def send_the_rems(message_to_be_sent):
    time.sleep(0.5)
    pyautogui.hotkey('ctrl')
    pyautogui.hotkey('ctrl','1')
    time.sleep(2)
    process_numbers(t7_output_file_path, message_to_be_sent) # Assumes t7_output_file_path is defined

# Utility function to clean up temporary files.
def delete_file(file_path):
    try:
        if os.path.isfile(file_path):
            os.remove(file_path)
            print(f"Deleted")
        else:
            print(f"File not found: {file_path}")
    except Exception as e:
        print(f"Error deleting file {file_path}: {e}")

