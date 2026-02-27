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

# Define file paths - this means provide the path to the templates and or other files that will be needed here 
# example: searchbox_template = "Users/Me/ScreenShots/abc123.png"
screenshot_path = "path/to/store/screenshots/at"
output_image_with_boxes = "path/to/store/marked/images/at"
output_image_with_boxes_and_grid = "path/to/store/marked/and/grid/applied/images/at"

# Highly recommmned to keep everything in a single folder with subfolders preferably to avoid mess

punctuation_to_remove = '"'

def take_screenshot(screenshot_path):
    # print("Capturing visuals...")
    screenshot = pyautogui.screenshot()
    screenshot.save(screenshot_path)

def display_combined_templates_and_boxes(screenshot_path, template_path, output_path):
    # print("Loading and displaying images...")
    # Load image and template
    image = cv2.imread(screenshot_path)
    template = cv2.imread(template_path, cv2.IMREAD_GRAYSCALE)
    # Check if image and template are loaded successfully
    if image is None or template is None:
        print("Error: Image or template could not be loaded")
        return
    # Convert template to uint8
    template = template.astype(np.uint8)
    # Check if template is larger than the image
    if template.shape[0] > image.shape[0] or template.shape[1] > image.shape[1]:
        print("Error: Template is larger than the image")
        return
    # Match template with image and draw box
    # print(" Analyzing and marking...")
    image_with_box = image.copy()  # Create a copy of the image for drawing box
    # Match template
    box, how_good = match_template(image_with_box, template, (0, 0, 255))  # Red box
    # Save image with matched box
    cv2.imwrite(output_path, image_with_box)
    return box, how_good

def match_template(image, template, color):
    # print(" Finding template...")
    # Convert image to grayscale if it has more than one channel
    gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    # Perform template matching
    result = cv2.matchTemplate(gray_image, template, cv2.TM_CCOEFF_NORMED)
    _, max_val, _, max_loc = cv2.minMaxLoc(result)
    # Draw rectangle around matched area
    h, w = template.shape[:2]  # Get height and width of template
    top_left = max_loc
    bottom_right = (top_left[0] + w, top_left[1] + h)
    cv2.rectangle(image, top_left, bottom_right, color, 2)
    return (top_left, bottom_right) , max_val

def draw_grid(image_path, output_path):
    image = cv2.imread(image_path)
    if image is None:
        print("Error: Image could not be loaded")
        # return
    h, w, _ = image.shape
    cv2.line(image, (w // 2, 0), (w // 2, h), (255, 255, 255), 1)  # Vertical line
    cv2.line(image, (0, h // 2), (w, h // 2), (255, 255, 255), 1)  # Horizontal line
    cv2.imwrite(output_path, image)

def get_grid_coordinates(box_coords):
    top_left, bottom_right = box_coords
    grid_x = top_left[0] // 2
    grid_y = top_left[1] // 2
    return grid_x, grid_y

def tap_coords(button_coordinates):
    # print('pressing')
    position = button_coordinates # Adjust this as needed
    pyautogui.click(position[0], position[1])

def search_and_get_tapped(path):
    time.sleep(0.5)
    take_screenshot(screenshot_path)
    collect,how_good=display_combined_templates_and_boxes(screenshot_path,path,output_image_with_boxes)
    draw_grid(output_image_with_boxes, output_image_with_boxes_and_grid)
    how_good=math.ceil(how_good)
    if how_good > 0.85:
        coords = get_grid_coordinates(collect)
        # if path == setng_template_path:
        tap_coords(coords)
    # print(how_good)
    return how_good

def is_whatsapp_running_on_mac():
    result = subprocess.run(['osascript', '-e', 'tell application "System Events" to (name of processes) contains "WhatsApp"'], capture_output=True, text=True)
    return result.stdout.strip() == 'true'

def is_whatsapp_running_on_windows():
    # Iterate over all running processes
    for process in psutil.process_iter(['name']):
        # Check for both the Windows (.exe) and Mac app names
        if process.info['name'] in ['WhatsApp.exe', 'WhatsApp']:
            return True
    return False

def open_whatsapp_on_mac():
    # print("Beginning")
    if is_whatsapp_running_on_mac():
        subprocess.run(['osascript', '-e', 'tell application "WhatsApp" to activate'])
    else:
        subprocess.Popen(["/Applications/WhatsApp.localized/WhatsApp.app/Contents/MacOS/WhatsApp"])
        time.sleep(3)  # Wait for WhatsApp to open
        subprocess.run(['osascript', '-e', 'tell application "System Events" to tell process "WhatsApp" to set frontmost to true'])
    # print("WhatsApp opened.")

def open_whatsapp_windows():
    current_os = platform.system()
    
    if current_os == "Darwin":  # This is Mac
        if is_whatsapp_running_on_mac():
            subprocess.run(['osascript', '-e', 'tell application "WhatsApp" to activate'])
        else:
            subprocess.Popen(["/Applications/WhatsApp.localized/WhatsApp.app/Contents/MacOS/WhatsApp"])
            time.sleep(3)
            subprocess.run(['osascript', '-e', 'tell application "System Events" to tell process "WhatsApp" to set frontmost to true'])
            
    elif current_os == "Windows":
        # Launching via protocol brings it to front or starts it
        subprocess.run(['cmd', '/c', 'start whatsapp://'], shell=True)
        time.sleep(5 if not is_whatsapp_running_on_windows() else 1)


#this is custom logic that hones in on a target message you want from a exported .txt file of your chat
def parse_messages_within_time_range(chat_lines, start_time, end_time):
    message_pattern = re.compile(r'\[(.*?)\] (.*?): (.*)', re.DOTALL)
    new_messages = []
    
    current_message = []
    capture = False
    for line in chat_lines:
        match = message_pattern.match(line)
        if match:
            timestamp_str, sender, message = match.groups()
            # print(timestamp_str)
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

# Function to filter messages containing a specific string
def filter_messages_with_string(file_path, output_file_path, search_string):
    filtered_messages = []
    most_recent_message = ''
    recm=0
    
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
    
    # Split messages by the custom delimiter (assuming each message ends with \n\n)
    messages = content.split('|')
    
    for message in messages:
        if search_string in message:
            if '-PHOTO-' in message or '-VIDEO-' in message or 'video omitted' in message or 'photo omitted' in message :
                bracket_index = message.find('[')
                # Split the message into two parts
                part1 = message[:bracket_index].strip()
                part2 = message[bracket_index:].strip()
                # Add both parts as separate messages
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

#To extract the .zip file of your chat, extract path is just the path to where that .zip file will be
def search_and_rescue(which_chat_to_rescue, ghanta,search_string):
    # Create directory for extraction if it doesn't exist
    if not os.path.exists(extract_path):
        os.makedirs(extract_path)

    # Unzip the file
    with zipfile.ZipFile(which_chat_to_rescue, 'r') as zip_ref:
        zip_ref.extractall(extract_path)

    # Read the extracted text file (assuming there's only one text file in the zip)
    chat_file_path = [os.path.join(extract_path, f) for f in os.listdir(extract_path) if f.endswith('.txt')][0]

    # Read chat file
    with open(chat_file_path, 'r', encoding='utf-8') as file:
        chat_lines = file.readlines()

    # User input date
    # user_input_date_str = input("Enter the date (dd/mm/yy): ")
    # user_input_date = datetime.strptime(user_input_date_str, '%d/%m/%y')
    # time.sleep(5)
    # # Define the time range based on user input
    # start_time = user_input_date.replace(hour=ghanta, minute=0, second=0, microsecond=0)  # 8 PM
    # end_time = user_input_date.replace(hour=23, minute=59, second=59, microsecond=99999)  # 11:59:59 PM

    # Uncomment the following lines to use the current date from the PC
    now = datetime.now()
    start_time = now.replace(hour=ghanta, minute=0, second=0, microsecond=0)  # 8 PM
    end_time = now.replace(hour=23, minute=59, second=59, microsecond=0)  # 11:59:59 PM

    # Parse new messages within the specified time range
    new_messages = parse_messages_within_time_range(chat_lines, start_time, end_time)

    # Save the new messages to the output file
    with open(output_file_path, 'w', encoding='utf-8') as file:
        for message in new_messages:
            file.write('|' + message + '|' + '\n\n')

    reminder, recm = filter_messages_with_string(output_file_path, fixed_output_file_path, search_string)
    return reminder, recm

def save_list_with_identifier(file_path, output_file_path, identifier, punctuation_to_remove):
    with open(file_path, 'r', encoding='utf-8') as file:
        lines = file.readlines()
    
    # Define translation table to remove punctuation
    translation_table = str.maketrans('', '', punctuation_to_remove)

    names = []
    for line in lines:
        normalized_line = re.sub(r'\s+', ' ', line)
        if identifier in normalized_line:
            name = normalized_line.split(identifier)[-1].strip()
            # Remove punctuation from the name
            name = name.translate(translation_table)
            names.append(name)
    
    with open(output_file_path, 'w', encoding='utf-8') as file:
        for name in names:
            file.write(name + '\n')


# Function to read names from a text file and get corresponding phone numbers, phone numbers to be stored in a dict and names from the file to be used as keys
def get_nums(file_path, output_file_path, name_dict):
    with open(file_path, 'r', encoding='utf-8') as file:
        names = [line.strip().upper() for line in file if line.strip()]  # Convert names to uppercase and remove empty lines
    
    with open(output_file_path, 'w', encoding='utf-8') as output_file:
        for name in names:
            phone_number = name_dict.get(name, 'Name not found')
            if phone_number != 'Name not found':
                output_file.write(f"{phone_number}\n")  # Write phone number to file if found
            else:
                output_file.write(f"{phone_number}\n")  # Write 'Name not found' if name is not in the dictionary

def just_paste():
    pyautogui.hotkey('command')
    pyautogui.hotkey('command', 'v')
    time.sleep(0.4)
    pyautogui.press('enter')

def tap_coordinates(x,y):
    group_area_position = (x,y) # Adjust this as needed
    pyautogui.click(group_area_position[0], group_area_position[1])
    time.sleep(1)

def paste_things(whattho,message_to_be_sent): 
    pyperclip.copy(whattho)
    search_and_get_tapped(search_box_template_path)
    just_paste()


def process_numbers(file_path,message_to_be_sent):
    with open(file_path, 'r', encoding='utf-8') as file:
        numbers = [line.strip() for line in file if line.strip()]  # Remove empty lines
    
    for number in numbers:
        if number != 'Name not found':
            paste_things(number,message_to_be_sent)

def send_the_rems(message_to_be_sent):
    time.sleep(0.5)
    pyautogui.hotkey('ctrl')
    pyautogui.hotkey('ctrl','1')
    time.sleep(2)
    process_numbers(t7_output_file_path,message_to_be_sent)

def delete_file(file_path):
    try:
        # Check if file exists
        if os.path.isfile(file_path):
            os.remove(file_path)
            print(f"Deleted")
        else:
            print(f"File not found: {file_path}")
    except Exception as e:
        print(f"Error deleting file {file_path}: {e}")

# This code provides the functions that will be used to perform the task, below is a guide on how to customize it to your use case.
