import pygame
import cv2
import numpy as np
import torch
from PIL import Image
from datetime import datetime
from transformers import AutoImageProcessor, AutoModelForDepthEstimation
from pygame import mixer
from camera_manager import CameraManager
import sys
from dotenv import load_dotenv

load_dotenv()

SCREEN_WIDTH = int(1280)
SCREEN_HEIGHT = int(745)
SCREEN_SIZE = (SCREEN_WIDTH, SCREEN_HEIGHT)

# Initialize Pygame
pygame.init()

BLACK = (0, 0, 0)
LIGHT_BLUE = (173, 216, 230)
WHITE = (255, 255, 255)
NAVY_BLUE = (20, 20, 40)
UI_GREEN = (18, 255, 18)
font = pygame.font.Font("resources/nebula-regular.otf", 30)

# Initialize the mixer
mixer.init()

# Initialize FastDepth model and processor
checkpoint = "depth-anything/Depth-Anything-V2-Small-hf"  # FastDepth model from Hugging Face
image_processor = AutoImageProcessor.from_pretrained(checkpoint)
model = AutoModelForDepthEstimation.from_pretrained(checkpoint)

# Move model to GPU if available
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model.to(device)

def play_sound(file_path):
    """Play a sound using pygame mixer."""
    try:
        mixer.music.load(file_path)
        mixer.music.play()
    except pygame.error as e:
        print(f"Error playing sound {file_path}: {e}")

def perform_depth_estimation(image, threshold=0.5):
    """Perform depth estimation using the FastDepth model and apply color threshold."""
    # Resize image to a smaller size for faster processing
    image_resized = image.resize((1280, 745))  # Resize to smaller dimensions for quicker inference
    pixel_values = image_processor(image_resized, return_tensors="pt").pixel_values.to(device)

    # Run depth estimation using the model on GPU or CPU
    with torch.no_grad():
        outputs = model(pixel_values)
        predicted_depth = outputs.predicted_depth.cpu().numpy()  # Move to CPU after inference

    # Normalize depth values to range [0, 255]
    min_depth = np.min(predicted_depth)
    max_depth = np.max(predicted_depth)
    if max_depth > min_depth:
        predicted_depth_normalized = (predicted_depth - min_depth) / (max_depth - min_depth) * 255
    else:
        predicted_depth_normalized = np.zeros_like(predicted_depth)

    predicted_depth_normalized = predicted_depth_normalized.astype(np.uint8)

    if len(predicted_depth_normalized.shape) == 3:
        predicted_depth_normalized = predicted_depth_normalized.squeeze()

    # Apply color map to the normalized depth values (depth map as color)
    depth_colored = cv2.applyColorMap(predicted_depth_normalized, cv2.COLORMAP_VIRIDIS)

    # Apply thresholding: everything above the threshold remains colored, the rest is black
    depth_gray = cv2.cvtColor(depth_colored, cv2.COLOR_BGR2GRAY)
    _, thresholded_image = cv2.threshold(depth_gray, threshold * 255, 255, cv2.THRESH_BINARY)

    # Mask the depth_colored image with the thresholded image
    thresholded_depth = cv2.bitwise_and(depth_colored, depth_colored, mask=thresholded_image)

    return thresholded_depth

def save_images(depth_map):
    """Save the depth map as an image."""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    depth_map_path = f'./scans/depth_map_{timestamp}.png'
    cv2.imwrite(depth_map_path, depth_map)
    print(f"Saved depth map as {depth_map_path}")

def run(screen, camera_manager):
    running = True
    depth_image = None
    scanning = False

    circle_radius = 100
    home_button_center = (50 + circle_radius, SCREEN_SIZE[1] - 50 - circle_radius)
    scan_button_rect = pygame.Rect((SCREEN_SIZE[0] // 2 - 150, SCREEN_SIZE[1] - 150, 300, 70))

    font = pygame.font.Font('resources/nebula-regular.otf', 36)

    while running:
        if not camera_manager.update():
            continue

        transformed_landmarks = camera_manager.get_transformed_landmarks()
        index_pos = None
        if transformed_landmarks:
            for hand_landmarks in transformed_landmarks:
                index_pos = (int(hand_landmarks[8][0]), int(hand_landmarks[8][1]))  # INDEX_FINGER_TIP

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                pygame.quit()
                sys.exit()

        screen.fill(BLACK)

        if index_pos:
            if scan_button_rect.collidepoint(index_pos):
                scanning = True
                depth_image = None  # Clear the previous depth map

                # Play start sound
                play_sound('audio/drawing.wav')

                # Run scanning animation
                for y in range(0, SCREEN_SIZE[1], 20):
                    screen.fill(BLACK)
                    pygame.draw.line(screen, WHITE, (0, y), (SCREEN_SIZE[0], y), 5)
                    pygame.display.flip()
                    pygame.time.delay(10)

                # Clear the scanning lines
                screen.fill(BLACK)
                pygame.display.flip()

                # Play end sound
                play_sound('audio/release.mp3')

                # Capture an image from the camera
                ret, frame = camera_manager.cap.read()
                if ret:
                    # Apply M1 transformation to the captured image
                    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    frame_transformed = cv2.warpPerspective(frame_rgb, camera_manager.M, (SCREEN_SIZE[0], SCREEN_SIZE[1]))
                    image = Image.fromarray(frame_transformed)
                    depth_colored = perform_depth_estimation(image, threshold=0.5)  # Set threshold to 0.5

                    # Save images
                    save_images(depth_colored)

                    depth_image = depth_colored

                scanning = False

            if (index_pos[0] - home_button_center[0])**2 + (index_pos[1] - home_button_center[1])**2 <= circle_radius**2:
                running = False

        if depth_image is not None:
            # Ensure the image is correctly converted to RGB format for Pygame
            depth_surface = pygame.surfarray.make_surface(depth_image.transpose((1, 0, 2)))
            depth_surface = pygame.transform.scale(depth_surface, (SCREEN_SIZE[0], SCREEN_SIZE[1]))
            screen.blit(depth_surface, (0, 0))

        # Draw a black bar at the bottom for hand tracking
        pygame.draw.rect(screen, BLACK, (0, SCREEN_SIZE[1] - 200, SCREEN_SIZE[0], 200))

        # Draw scan button
        pygame.draw.rect(screen, NAVY_BLUE, scan_button_rect, border_radius=15)
        pygame.draw.rect(screen, UI_GREEN, scan_button_rect, 5, border_radius=15)
        button_text = 'Scanning...' if scanning else 'Start Scan'
        text_surface = font.render(button_text, True, UI_GREEN)
        text_rect = text_surface.get_rect(center=scan_button_rect.center)
        screen.blit(text_surface, text_rect)

        # Draw home button
        pygame.draw.circle(screen, NAVY_BLUE, home_button_center, circle_radius)
        pygame.draw.circle(screen, UI_GREEN, home_button_center, circle_radius, 5)
        text_surface = font.render('Home', True, UI_GREEN)
        text_rect = text_surface.get_rect(center=home_button_center)
        screen.blit(text_surface, text_rect)

        # Draw the hand tracking circle on top of everything
        if index_pos:
            pygame.draw.circle(screen, LIGHT_BLUE, index_pos, 10, 3)

        pygame.display.flip()
        pygame.time.delay(1)
