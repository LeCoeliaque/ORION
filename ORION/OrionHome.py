
import pygame
from pygame import mixer
import time
import os
import sys
import math
from camera_manager import CameraManager
from dotenv import load_dotenv
from apps.app_2 import app_2
# Set the window position to your second monitor (adjust based on your setup)
os.environ['SDL_VIDEO_WINDOW_POS'] = '1920,0'  # Assuming second monitor starts at x=1920

load_dotenv()

# Initialize Pygame
pygame.init()
# Initialize the mixer
mixer.init()

# Constants
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 745
SCREEN_SIZE = (SCREEN_WIDTH, SCREEN_HEIGHT)
NAVY_BLUE = (20, 20, 40)
LIGHT_BLUE = (173, 216, 230)
UI_GREEN= (18,255,18)
RED = (255, 0, 0)
font= pygame.font.Font('resources/nebula-regular.otf', 80)
app_font= pygame.font.Font('resources/nebula-regular.otf', 50)
text = 'Home'
rect_x, rect_y, rect_height, rect_width = 100,100, 100,300
rect_bounds= rect_x, rect_y, rect_width, rect_height
home =pygame.Rect(rect_bounds)
startup_image = pygame.image.load('BuildcaveStartup.png')
image_width, image_height = startup_image.get_size()
center_x = (SCREEN_WIDTH - image_width) // 2
center_y = (SCREEN_HEIGHT - image_height) // 2
rect_cx= 450
rect_cy=120
apps_visible=False
#Flags
home_open= False
home_toggle_delay = 1
# Function to play sound

def play_sound(file_path):
    """Play sound from the specified file path."""
    try:
        mixer.music.load(file_path)
        mixer.music.play()
    except Exception as e:
        print(f"Error playing sound: {e}")


class AppCircle:
    def __init__(self, center, radius, app_index):
        self.center = center
        self.radius = radius
        self.app_index = app_index
        self.text = f'App {app_index}'
        self.image = self.load_image()

    def load_image(self):
        """Load app image if available."""
        image_path = f'./apps/app_{self.app_index}.jpg'
        if os.path.exists(image_path):
            image = pygame.image.load(image_path)
            return pygame.transform.scale(image, (2 * self.radius, 2 * self.radius))
        return None

    
def draw_app(screen, rect_width, rect_height, color, outline_width):
    pygame.draw.rect(screen, UI_GREEN, pygame.Rect(rect_cx, rect_cy, rect_width, rect_height), outline_width)
    pygame.draw.rect(screen, UI_GREEN, pygame.Rect(rect_cx+300, rect_cy, rect_width, rect_height), outline_width)
    text_surface = app_font.render(('RULER'), True, (UI_GREEN))
    text_width, text_height= text_surface.get_size()
    text_x,text_y= (rect_cx+ (rect_width-text_width)//2 +5), (rect_cy+(rect_height-text_height)//2 -5)
    screen.blit(text_surface, (text_x, text_y))

def run_ace_home(screen, camera_manager):
    global home_open, home_toggle_delay, apps_visible
    apps =[]
    running = True
    last_home_toggle=time.time()
    screen.blit(startup_image, (center_x, center_y))
    ruler=pygame.Rect(rect_cx, rect_cy, rect_width, rect_height)
    scan=pygame.Rect(rect_cx+350, rect_cy, rect_width, rect_height)
    play_sound("./audio/startup.mp3")
    pygame.display.flip()
    pygame.time.wait(3000)
    


    while running:
        if not camera_manager.update():
            continue

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                camera_manager.release()
                sys.exit()

        # Fill the background and draw all circles
        screen.fill((0, 0, 0))  # Clear the screen
        index_finger_pos = None
        


        transformed_landmarks = camera_manager.get_transformed_landmarks()
        if transformed_landmarks:
            for transformed_coords in transformed_landmarks:
                index_finger_tip = transformed_coords[camera_manager.mp_hands.HandLandmark.INDEX_FINGER_TIP]
                screen_x, screen_y = int(index_finger_tip[0]), int(index_finger_tip[1])
                index_finger_pos = (screen_x, screen_y)


        pygame.draw.rect(screen, UI_GREEN, (rect_x, rect_y, rect_width, rect_height), 5)
        text_surface = font.render(text, True, (UI_GREEN))
        text_width, text_height= text_surface.get_size()
        text_x,text_y= (rect_x+ (rect_width-text_width)//2 +5), (rect_y+(rect_height-text_height)//2 -5)
        screen.blit(text_surface, (text_x, text_y))
        if index_finger_pos is not None:
            if home.collidepoint(index_finger_pos):
                if time.time() - last_home_toggle >home_toggle_delay:
                    if not home_open:
                        print("home open")
                        home_open= True
                        last_home_toggle=time.time()
                        apps_visible=True
                        pygame.draw.rect(screen, UI_GREEN, (500, 100, rect_width, rect_height), 5)
                        play_sound("./audio/button.mp3")
                    else:
                        if home_open:
                            apps_visible=False
                            play_sound("./audio/back.mp3")
                            home_open=False
                            last_home_toggle=time.time()
                            print('home close')

            elif home.collidepoint(index_finger_pos) and home_open:
            
                home_open=False
        
             
     

        if apps_visible:
                draw_app(screen, 250, 60, UI_GREEN, 5)
                text_surface = app_font.render(('SCAN'), True, (UI_GREEN))
                text_width, text_height= text_surface.get_size()
                text_x,text_y= ((rect_cx+275)+ (rect_width-text_width)//2 +5), (100+(rect_height-text_height)//2 -5)
                screen.blit(text_surface, (text_x, text_y))

        if index_finger_pos is not None:
                if ruler.collidepoint(index_finger_pos):
                    
                    try:
                        app = f'app_{1}.app_{1}'
                        print(f"Launching app: {app}")
                        mod = __import__(f'apps.{app}', fromlist=[''])
                        play_sound("./audio/confirmation.wav")
                        mod.run(screen, camera_manager)  # Pass camera_manager to the app
                                                
                    except ModuleNotFoundError:
                        print(f"Module 'apps.{app}' not found.")
                        play_sound("./audio/reject.wav")  
                if scan.collidepoint(index_finger_pos): 
                    try:
                        app = f'app_{2}.app_{2}'
                        print(f"Launching app: {app}")
                        mod = __import__(f'apps.{app}', fromlist=[''])
                        play_sound("./audio/confirmation.wav")
                        mod.run(screen, camera_manager)  # Pass camera_manager to the app
                                                
                    except ModuleNotFoundError:
                        print(f"Module 'apps.{app}' not found.")
                        play_sound("./audio/reject.wav")     

        if index_finger_pos:
            pygame.draw.circle(screen, LIGHT_BLUE, index_finger_pos, 15, 3)
        

        pygame.display.flip()
        pygame.time.delay(10)


if __name__ == '__main__':
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.FULLSCREEN)
    pygame.display.set_caption('Home Screen')

    camera_manager = CameraManager('./M.npy', SCREEN_WIDTH, SCREEN_HEIGHT)
    run_ace_home(screen, camera_manager)