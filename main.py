import pygame
import numpy as np
import sounddevice as sd
import soundfile as sf
import pmma

pmma.init()

# Load audio file
filename = "Austin John's Park Bench V2.mp3"
data, samplerate = sf.read(filename)
data = data.mean(axis=1) if data.ndim > 1 else data  # Convert to mono if stereo
max_amplitude = np.max(np.abs(data)) ** 2 # Find maximum amplitude for normalization

# Pygame setup
pygame.init()
window_width = 1280
window_height = 720
screen = pygame.display.set_mode((window_width, window_height))
clock = pygame.time.Clock()

# Line parameters
line_color = (0, 255, 0)
line_thickness = 2

# Buffer for real-time volume data
volume_buffer = [0] * window_width

# Shared variable for playback position
playback_position = 0
volume = 0

# Sound playback callback
def audio_callback(outdata, frames, time, status):
    global playback_position, volume_buffer, volume

    # Compute the start and end frame indices
    start_frame = playback_position
    end_frame = start_frame + frames

    # Ensure the indices don't exceed the audio data length
    if start_frame >= len(data):
        chunk = np.zeros((frames,), dtype=data.dtype)  # Fill with silence
    else:
        chunk = data[start_frame:end_frame]

        # If the chunk is smaller than the requested frames, pad it with zeros
        if len(chunk) < frames:
            chunk = np.pad(chunk, (0, frames - len(chunk)))

    # Normalize volume
    volume = np.max(np.abs(chunk)) / max_amplitude if len(chunk) > 0 else 0
    volume = volume ** 2

    # Fill the output buffer with the audio data
    outdata[:] = np.expand_dims(chunk, axis=1)

    # Update playback position
    playback_position += frames

# Open a sounddevice output stream
stream = sd.OutputStream(samplerate=samplerate, channels=1, callback=audio_callback)
stream.start()

player_height = window_height/2
player_points = []
up = False
# Game loop
running = True
t = 0
while running:
    # Update volume buffer
    v = volume
    prev_vol = (volume_buffer[-1] * 0.6 + v) / 2
    n = 7
    for _ in range(n):
        volume_buffer.pop(0)
        volume_buffer.append(prev_vol * (1 - (1/n)) + v * (1/n))

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                up = True
        if event.type == pygame.KEYUP:
            if event.key == pygame.K_SPACE:
                up = False

    # Clear the screen
    screen.fill((0, 0, 0))

    if up:
        player_height -= 4
    else:
        player_height += 4

    if player_height < 0:
        player_height = 0
    elif player_height > window_height:
        player_height = window_height

    for _ in range(7):
        if len(player_points) > window_width / 2:
            player_points.pop(0)
        player_points.append(player_height)

    if len(player_points) > 1:
        points = []
        for x, y in enumerate(player_points):
            points.append((x, y))
        pygame.draw.lines(screen, (255, 0, 0), False, points, line_thickness)

    # Draw the volume line
    top_points = [(0, 0)]
    bottom_points = [(0, window_height)]
    for x, v in enumerate(volume_buffer):
        top_mag = v * ((window_height - 25) / 2)
        bottom_mag = v * ((window_height - 25) / 2)
        top_points.append((x, top_mag))
        bottom_points.append((x, window_height - (bottom_mag)))
    t += 1

    top_points.append((window_width, 0))
    bottom_points.append((window_width, window_height))

    if len(top_points) > 1:
        pygame.draw.polygon(screen, line_color, top_points)
        pygame.draw.polygon(screen, line_color, bottom_points)

    pmma.compute()

    pygame.display.flip()
    clock.tick(60)

# Cleanup
stream.stop()
stream.close()
pygame.quit()
