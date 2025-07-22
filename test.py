import flet as ft


def main(page: ft.Page):
    page.title = "Simple Audio Recorder"
    page.theme_mode = ft.ThemeMode.DARK
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.window_width = 600
    page.window_height = 400
    
    # Status text
    status_text = ft.Text("Ready to record", size=16)
    
    # Audio recorder control
    audio_recorder = ft.AudioRecorder(
        on_state_changed=lambda e: on_state_changed(e, status_text)
    )
    page.overlay.append(audio_recorder)
    
    def on_state_changed(e, status):
        """Handle audio recorder state changes"""
        if e.data == "recording":
            status.value = "🔴 Recording..."
        elif e.data == "stopped":
            status.value = "⏹️ Recording stopped"
        elif e.data == "paused":
            status.value = "⏸️ Recording paused"
        else:
            status.value = f"Status: {e.data}"
        page.update()
    
    def start_recording(e):
        """Start recording"""
        import os
        # Create recordings directory if it doesn't exist
        recordings_dir = os.path.join(os.path.expanduser("~"), "Desktop", "Recordings")
        os.makedirs(recordings_dir, exist_ok=True)
        
        # Generate unique filename
        import datetime
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = os.path.join(recordings_dir, f"recording_{timestamp}.wav")
        
        audio_recorder.start_recording(output_path=output_path)
    
    def stop_recording(e):
        """Stop recording"""
        audio_recorder.stop_recording()
    
    def pause_recording(e):
        """Pause recording"""
        audio_recorder.pause_recording()
    
    def resume_recording(e):
        """Resume recording"""
        audio_recorder.resume_recording()
    
    # Create UI
    page.add(
        ft.Text("Simple Audio Recorder", size=24, weight=ft.FontWeight.BOLD),
        ft.Container(height=20),
        status_text,
        ft.Container(height=30),
        ft.Row([
            ft.ElevatedButton(
                "🎤 Start Recording",
                on_click=start_recording,
                color=ft.Colors.WHITE,
                bgcolor=ft.Colors.RED_400
            ),
            ft.ElevatedButton(
                "⏹️ Stop",
                on_click=stop_recording,
                color=ft.Colors.WHITE,
                bgcolor=ft.Colors.GREY_600
            ),
        ], alignment=ft.MainAxisAlignment.CENTER, spacing=20),
        ft.Container(height=20),
        ft.Row([
            ft.ElevatedButton(
                "⏸️ Pause",
                on_click=pause_recording,
                color=ft.Colors.WHITE,
                bgcolor=ft.Colors.ORANGE_400
            ),
            ft.ElevatedButton(
                "▶️ Resume",
                on_click=resume_recording,
                color=ft.Colors.WHITE,
                bgcolor=ft.Colors.GREEN_400
            ),
        ], alignment=ft.MainAxisAlignment.CENTER, spacing=20),
    )


if __name__ == "__main__":
    ft.app(target=main)
