import pygame
import numpy as np
import threading
import time


class AlarmSound:
    def __init__(self):
        pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
        self.is_playing = False
        self.sound_thread = None
        self.alarm_sound = self._generate_alarm_sound()
    
    def _generate_alarm_sound(self):
        """Generate a simple beep alarm sound"""
        sample_rate = 22050
        duration = 0.5  # 0.5 seconds
        frequency = 800  # 800 Hz beep
        
        # Generate sine wave
        frames = int(duration * sample_rate)
        arr = np.zeros((frames, 2))
        
        for i in range(frames):
            wave = np.sin(2 * np.pi * frequency * i / sample_rate)
            # Apply envelope to avoid clicks
            envelope = min(i / (sample_rate * 0.01), 1.0, (frames - i) / (sample_rate * 0.01))
            arr[i] = [wave * envelope * 0.3, wave * envelope * 0.3]  # Stereo, reduced volume
        
        # Convert to pygame sound
        arr = (arr * 32767).astype(np.int16)
        sound = pygame.sndarray.make_sound(arr)
        return sound
    
    def start_alarm(self):
        """Start playing the alarm sound in a loop"""
        if not self.is_playing:
            self.is_playing = True
            self.sound_thread = threading.Thread(target=self._play_loop)
            self.sound_thread.daemon = True
            self.sound_thread.start()
    
    def stop_alarm(self):
        """Stop playing the alarm sound"""
        self.is_playing = False
        pygame.mixer.stop()
    
    def _play_loop(self):
        """Play the alarm sound in a loop until stopped"""
        while self.is_playing:
            if self.is_playing:  # Check again in case it was stopped
                self.alarm_sound.play()
                time.sleep(0.7)  # Wait a bit between beeps (0.5s sound + 0.2s pause)
    
    def cleanup(self):
        """Clean up pygame mixer"""
        self.stop_alarm()
        pygame.mixer.quit()
