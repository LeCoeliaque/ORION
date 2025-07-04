import pygame
from pygame import mixer
import sys
import time
import math
from camera_manager import CameraManager
from dotenv import load_dotenv
import os

load_dotenv()
# Initialize Pygame
pygame.init()
# Initialize the mixer
mixer.init()
SCREEN_WIDTH = int(1280)
SCREEN_HEIGHT = int(745)
SCREEN_SIZE = (SCREEN_WIDTH, SCREEN_HEIGHT)
BLACK = (0, 0, 0)
LIGHT_BLUE = (173, 216, 230)
WHITE = (255, 255, 255)
NAVY_BLUE = (20, 20, 40)
UI_GREEN=(18, 255, 18)
PIXEL_TO_MM = 0.568750 #adjust as needed
PINCH_RELEASE_DISTANCE = 700 # Distance to release the pinch
PINCH_HOLD_TIME = 1  # Minimum time to hold the pinch before releasing

def distance(p1, p2):
    return math.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)

def play_sound(file_path):
        sound= mixer.Sound(file_path)
        sound.play()

def draw_line_with_measurement(screen, start_point, end_point):
    if start_point and end_point:
        pygame.draw.line(screen, LIGHT_BLUE, start_point, end_point, 2)
        pygame.draw.circle(screen, LIGHT_BLUE, start_point, 5)
        pygame.draw.circle(screen, LIGHT_BLUE, end_point, 5)
        mid_line_point = ((start_point[0] + end_point[0]) // 2, (start_point[1] + end_point[1]) // 2)
        line_length = distance(start_point, end_point) * PIXEL_TO_MM
        font = pygame.font.Font(None, 36)
        text_surface = font.render(f'{line_length:.2f} mm', True, WHITE)
        screen.blit(text_surface, mid_line_point)

def run(screen, camera_manager):
    running = True
    drawing = False
    start_point = None
    end_point = None
    permanent_lines = []
    pinch_start_time = None

    home_button_rect = pygame.Rect(50,50,150,50)  # Moved farther right and down
 

    clear_button_rect = pygame.Rect((SCREEN_SIZE[0]  - 400, 50, 300, 70))

    while running:
        if not camera_manager.update():
            continue

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                pygame.quit()
                camera_manager.release()
                sys.exit()

        screen.fill(BLACK)

        transformed_landmarks = camera_manager.get_transformed_landmarks()
        if transformed_landmarks:
            for hand_landmarks in transformed_landmarks:
                thumb_pos = (int(hand_landmarks[4][0]), int(hand_landmarks[4][1]))  # THUMB_TIP
                index_pos = (int(hand_landmarks[8][0]), int(hand_landmarks[8][1]))  # INDEX_FINGER_TIP

                mid_point = ((thumb_pos[0] + index_pos[0]) // 2, (thumb_pos[1] + index_pos[1]) // 2)
                pygame.draw.circle(screen, LIGHT_BLUE, mid_point, 10, 3)

                pygame.draw.circle(screen, WHITE, thumb_pos, 5)
                pygame.draw.circle(screen, WHITE, index_pos, 5)

                distance_between_fingers = distance(thumb_pos, index_pos)
                if distance_between_fingers < 50:  # Threshold for starting a pinch
                    pygame.draw.circle(screen, WHITE, mid_point, 10)
                    if not drawing:
                        
                        start_point = mid_point
                        drawing = True
                        pinch_start_time = time.time()
                        play_sound('audio/drawing.mp3')
                    else:
                        end_point = mid_point
                else:
                    if drawing and (distance_between_fingers > PINCH_RELEASE_DISTANCE or (time.time() - pinch_start_time) > PINCH_HOLD_TIME):
                        if start_point and end_point:
                            play_sound('audio/release.mp3')
                            permanent_lines.append((start_point, end_point))
                        drawing = False

        for line in permanent_lines:
            draw_line_with_measurement(screen, line[0], line[1])

        if drawing and start_point and end_point:
            draw_line_with_measurement(screen, start_point, end_point)

        # Check if the cursor touches the home button or the clear button
        if index_pos and home_button_rect.collidepoint(index_pos):
            running = False
            play_sound('audio/back.mp3')
            screen.fill((0,0,0))
        elif index_pos and clear_button_rect.collidepoint(index_pos):
            permanent_lines = []

        # Draw home button
        pygame.draw.rect(screen, UI_GREEN, (home_button_rect), 5)
       
        font = pygame.font.Font('resources/nebula-regular.otf', 36)
        text_surface = font.render('Home', True, UI_GREEN)
        text_rect = text_surface.get_rect(center=home_button_rect.center)
        screen.blit(text_surface, text_rect)

        # Draw clear button
        
        pygame.draw.rect(screen, UI_GREEN, clear_button_rect, 5, border_radius=15)
        text_surface = font.render('Clear', True, UI_GREEN)
        text_rect = text_surface.get_rect(center=clear_button_rect.center)
        screen.blit(text_surface, text_rect)

        pygame.display.flip()
        pygame.time.delay(1)

