import flet as ft
import threading
import time
import argparse
from alarm_sound import AlarmSound


class TimerApp:
    def __init__(self, page: ft.Page, initial_seconds=None):
        self.page = page
        self.page.title = "Timer"
        self.page.theme_mode = ft.ThemeMode.LIGHT
        self.page.vertical_alignment = ft.MainAxisAlignment.CENTER
        self.page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
        self.page.window.width = 400
        self.page.window.height = 450
        self.page.window.resizable = False
        
        # Timer state
        self.total_seconds = 0
        self.is_running = False
        self.timer_thread = None
        self.alarm = AlarmSound()
        self.alarm_active = False
        self.initial_seconds = initial_seconds
        
        # UI components
        self.time_display = ft.Text(
            "00:00:00",
            size=48,
            weight=ft.FontWeight.BOLD,
            color=ft.Colors.BLUE_700
        )
        
        self.minutes_input = ft.TextField(
            label="Minutes",
            value="5",
            width=100,
            keyboard_type=ft.KeyboardType.NUMBER
        )
        
        self.seconds_input = ft.TextField(
            label="Seconds",
            value="0",
            width=100,
            keyboard_type=ft.KeyboardType.NUMBER
        )
        
        self.start_button = ft.ElevatedButton(
            "Start",
            on_click=self.start_timer,
            color=ft.Colors.WHITE,
            bgcolor=ft.Colors.GREEN_600
        )
        
        self.stop_button = ft.ElevatedButton(
            "Stop",
            on_click=self.stop_timer,
            color=ft.Colors.WHITE,
            bgcolor=ft.Colors.RED_600,
            disabled=True
        )
        
        self.reset_button = ft.ElevatedButton(
            "Reset",
            on_click=self.reset_timer,
            color=ft.Colors.WHITE,
            bgcolor=ft.Colors.BLUE_600
        )
        
        self.dismiss_button = ft.ElevatedButton(
            "Dismiss Alarm",
            on_click=self.dismiss_alarm,
            color=ft.Colors.WHITE,
            bgcolor=ft.Colors.ORANGE_600,
            visible=False
        )
        
        self.setup_ui()
    
    def setup_ui(self):
        # Input row
        input_row = ft.Row(
            [
                self.minutes_input,
                ft.Text(":", size=20),
                self.seconds_input
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=10
        )
        
        # Button row
        button_row = ft.Row(
            [
                self.start_button,
                self.stop_button,
                self.reset_button
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=20
        )
        
        # Dismiss button row (separate for better layout)
        dismiss_row = ft.Row(
            [self.dismiss_button],
            alignment=ft.MainAxisAlignment.CENTER
        )
        
        # Main container
        main_container = ft.Container(
            content=ft.Column(
                [
                    self.time_display,
                    ft.Divider(height=20, color=ft.Colors.TRANSPARENT),
                    input_row,
                    ft.Divider(height=20, color=ft.Colors.TRANSPARENT),
                    button_row,
                    dismiss_row
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=10
            ),
            padding=40,
            border_radius=10,
            bgcolor=ft.Colors.WHITE,
            shadow=ft.BoxShadow(
                spread_radius=1,
                blur_radius=15,
                color=ft.Colors.BLUE_GREY_300,
                offset=ft.Offset(0, 0),
                blur_style=ft.ShadowBlurStyle.OUTER,
            )
        )
        
        self.page.add(main_container)
        
        # Auto-start timer if initial_seconds is provided
        if self.initial_seconds is not None:
            self.auto_setup_timer()
    
    def auto_setup_timer(self):
        """Automatically set up and start timer based on initial_seconds"""
        minutes = self.initial_seconds // 60
        seconds = self.initial_seconds % 60
        
        # Update input fields
        self.minutes_input.value = str(minutes)
        self.seconds_input.value = str(seconds)
        
        # Set total seconds and start timer
        self.total_seconds = self.initial_seconds
        self.is_running = True
        self.start_button.disabled = True
        self.stop_button.disabled = False
        self.minutes_input.disabled = True
        self.seconds_input.disabled = True
        
        # Start timer thread
        self.timer_thread = threading.Thread(target=self.run_timer)
        self.timer_thread.daemon = True
        self.timer_thread.start()
        
        # Update the page
        self.page.update()
    
    def start_timer(self, e):
        if not self.is_running:
            try:
                minutes = int(self.minutes_input.value or 0)
                seconds = int(self.seconds_input.value or 0)
                self.total_seconds = minutes * 60 + seconds
                
                if self.total_seconds > 0:
                    self.is_running = True
                    self.start_button.disabled = True
                    self.stop_button.disabled = False
                    self.minutes_input.disabled = True
                    self.seconds_input.disabled = True
                    
                    self.timer_thread = threading.Thread(target=self.run_timer)
                    self.timer_thread.daemon = True
                    self.timer_thread.start()
                    
                    self.page.update()
            except ValueError:
                self.show_error("Please enter valid numbers")
    
    def stop_timer(self, e):
        self.is_running = False
        self.start_button.disabled = False
        self.stop_button.disabled = True
        self.minutes_input.disabled = False
        self.seconds_input.disabled = False
        self.dismiss_alarm(None)  # Stop alarm if running
        self.page.update()
    
    def reset_timer(self, e):
        self.is_running = False
        self.total_seconds = 0
        self.time_display.value = "00:00:00"
        self.time_display.color = ft.Colors.BLUE_700
        self.start_button.disabled = False
        self.stop_button.disabled = True
        self.minutes_input.disabled = False
        self.seconds_input.disabled = False
        self.minutes_input.value = "5"
        self.seconds_input.value = "0"
        self.dismiss_alarm(None)  # Stop alarm if running
        self.page.update()
    
    def run_timer(self):
        while self.is_running and self.total_seconds > 0:
            self.update_display()
            time.sleep(1)
            self.total_seconds -= 1
        
        if self.total_seconds <= 0 and self.is_running:
            self.timer_finished()
    
    def update_display(self):
        hours = self.total_seconds // 3600
        minutes = (self.total_seconds % 3600) // 60
        seconds = self.total_seconds % 60
        
        self.time_display.value = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        self.page.update()
    
    def timer_finished(self):
        self.is_running = False
        self.time_display.value = "00:00:00"
        self.time_display.color = ft.Colors.RED_600
        self.start_button.disabled = False
        self.stop_button.disabled = True
        self.minutes_input.disabled = False
        self.seconds_input.disabled = False
        
        # Start alarm sound
        self.alarm_active = True
        self.alarm.start_alarm()
        self.dismiss_button.visible = True
        
        # Show completion message
        self.page.snack_bar = ft.SnackBar(
            content=ft.Text("Timer finished! Click 'Dismiss Alarm' to stop the sound.", color=ft.Colors.WHITE),
            bgcolor=ft.Colors.GREEN_600
        )
        self.page.snack_bar.open = True
        
        self.page.update()
    
    def dismiss_alarm(self, e):
        """Dismiss the alarm sound and hide the dismiss button"""
        if self.alarm_active:
            self.alarm_active = False
            self.alarm.stop_alarm()
            self.dismiss_button.visible = False
            self.time_display.color = ft.Colors.BLUE_700
            self.page.update()
    
    def show_error(self, message):
        self.page.snack_bar = ft.SnackBar(
            content=ft.Text(message, color=ft.Colors.WHITE),
            bgcolor=ft.Colors.RED_600
        )
        self.page.snack_bar.open = True
        self.page.update()


def main(page: ft.Page):
    # Get command-line arguments
    parser = argparse.ArgumentParser(description='Timer Application')
    parser.add_argument('--set', type=int, help='Set timer duration in seconds and start automatically')
    args = parser.parse_args()
    
    # Create timer app with optional initial seconds
    app = TimerApp(page, initial_seconds=args.set)


if __name__ == "__main__":
    ft.app(target=main)
