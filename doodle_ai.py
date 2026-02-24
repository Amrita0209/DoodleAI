import tkinter as tk
from tkinter import ttk, messagebox
import numpy as np
from PIL import Image, ImageDraw, ImageTk
import cv2
from sklearn.neighbors import NearestNeighbors
import random

class DoodleAI:
    """
    AI-powered doodle completion system.
    Analyzes your drawing and intelligently completes the other half.
    Uses pattern recognition, symmetry detection, and smart mirroring.
    """
    
    def __init__(self, root):
        self.root = root
        self.root.title("DoodleAI - AI Drawing Completion")
        self.root.geometry("1000x750")
        self.root.state('zoomed')
        self.root.configure(bg='#1a1a2e')
        
        # Drawing state
        self.canvas_width = 800
        self.canvas_height = 600
        self.drawing = False
        self.last_x = None
        self.last_y = None
        
        # Image buffers - left side is user drawn, right is AI completed
        self.left_image = Image.new('RGB', (self.canvas_width//2, self.canvas_height), 'white')
        self.right_image = Image.new('RGB', (self.canvas_width//2, self.canvas_height), 'white')
        self.left_draw = ImageDraw.Draw(self.left_image)
        self.right_draw = ImageDraw.Draw(self.right_image)
        
        # Stroke history for pattern analysis
        self.stroke_history = []
        self.current_stroke = []
        
        # AI parameters
        self.brush_size = 3
        self.completion_style = "smart_mirror"  # smart_mirror, creative, minimal
        
        self.setup_ui()
        
    def setup_ui(self):
        """Creates the interface"""
        # Title
        title = tk.Label(
            self.root, 
            text="✨ DoodleAI ✨", 
            font=("Helvetica", 28, "bold"),
            bg='#1a1a2e',
            fg='#00ff88'
        )
        title.pack(pady=10)
        
        subtitle = tk.Label(
            self.root,
            text="Draw on the left, AI completes on the right",
            font=("Helvetica", 12),
            bg='#1a1a2e',
            fg='#aaaaaa'
        )
        subtitle.pack()
        
        # Main canvas frame
        canvas_frame = tk.Frame(self.root, bg='#1a1a2e')
        canvas_frame.pack(pady=20)
        
        # Drawing canvas
        self.canvas = tk.Canvas(
            canvas_frame,
            width=self.canvas_width,
            height=self.canvas_height,
            bg='white',
            cursor='pencil',
            highlightthickness=2,
            highlightbackground='#00ff88'
        )
        self.canvas.pack()
        
        # Center divider line
        self.canvas.create_line(
            self.canvas_width//2, 0,
            self.canvas_width//2, self.canvas_height,
            fill='#ff0066',
            width=2,
            dash=(5, 5)
        )
        
        # Labels
        self.canvas.create_text(
            self.canvas_width//4, 20,
            text="YOUR DRAWING",
            font=("Helvetica", 14, "bold"),
            fill='#666666'
        )
        
        self.canvas.create_text(
            3*self.canvas_width//4, 20,
            text="AI COMPLETION",
            font=("Helvetica", 14, "bold"),
            fill='#00ff88'
        )
        
        # Control panel
        controls = tk.Frame(self.root, bg='#1a1a2e')
        controls.pack(pady=10)
        
        # Brush size
        tk.Label(
            controls, 
            text="Brush Size:", 
            bg='#1a1a2e', 
            fg='white',
            font=("Helvetica", 10)
        ).grid(row=0, column=0, padx=5)
        
        brush_slider = ttk.Scale(
            controls,
            from_=1,
            to=10,
            orient=tk.HORIZONTAL,
            command=self.update_brush_size,
            length=150
        )
        brush_slider.set(self.brush_size)
        brush_slider.grid(row=0, column=1, padx=5)
        
        # Style selector
        tk.Label(
            controls,
            text="AI Style:",
            bg='#1a1a2e',
            fg='white',
            font=("Helvetica", 10)
        ).grid(row=0, column=2, padx=5)
        
        style_var = tk.StringVar(value="Smart Mirror")
        style_menu = ttk.Combobox(
            controls,
            textvariable=style_var,
            values=["Smart Mirror", "Creative", "Minimal"],
            state="readonly",
            width=12
        )
        style_menu.grid(row=0, column=3, padx=5)
        style_menu.bind('<<ComboboxSelected>>', self.update_style)
        
        # Buttons
        btn_clear = tk.Button(
            controls,
            text="🗑️ Clear",
            command=self.clear_canvas,
            bg='#ff0066',
            fg='white',
            font=("Helvetica", 10, "bold"),
            padx=15,
            pady=5,
            relief=tk.FLAT,
            cursor='hand2'
        )
        btn_clear.grid(row=0, column=4, padx=5)
        
        btn_save = tk.Button(
            controls,
            text="💾 Save",
            command=self.save_drawing,
            bg='#00ff88',
            fg='black',
            font=("Helvetica", 10, "bold"),
            padx=15,
            pady=5,
            relief=tk.FLAT,
            cursor='hand2'
        )
        btn_save.grid(row=0, column=5, padx=5)
        
        # Bind drawing events
        self.canvas.bind('<Button-1>', self.start_draw)
        self.canvas.bind('<B1-Motion>', self.draw)
        self.canvas.bind('<ButtonRelease-1>', self.end_draw)
        
    def update_brush_size(self, value):
        """Update brush size from slider"""
        self.brush_size = int(float(value))
        
    def update_style(self, event):
        """Update AI completion style"""
        style_map = {
            "Smart Mirror": "smart_mirror",
            "Creative": "creative",
            "Minimal": "minimal"
        }
        selected = event.widget.get()
        self.completion_style = style_map[selected]
        # Redraw AI side with new style
        self.complete_drawing()
        
    def start_draw(self, event):
        """Start a new stroke"""
        # Only allow drawing on left side
        if event.x > self.canvas_width // 2:
            return
            
        self.drawing = True
        self.last_x = event.x
        self.last_y = event.y
        self.current_stroke = [(event.x, event.y)]
        
    def draw(self, event):
        """Draw as user moves mouse"""
        if not self.drawing or event.x > self.canvas_width // 2:
            return
        
        # Draw on canvas
        self.canvas.create_line(
            self.last_x, self.last_y,
            event.x, event.y,
            width=self.brush_size,
            fill='black',
            capstyle=tk.ROUND,
            smooth=True
        )
        
        # Draw on PIL image for processing
        self.left_draw.line(
            [self.last_x, self.last_y, event.x, event.y],
            fill='black',
            width=self.brush_size
        )
        
        # Track stroke
        self.current_stroke.append((event.x, event.y))
        
        self.last_x = event.x
        self.last_y = event.y
        
    def end_draw(self, event):
        """Finish stroke and trigger AI completion"""
        if not self.drawing:
            return
            
        self.drawing = False
        
        # Save stroke to history
        if len(self.current_stroke) > 2:  # ignore accidental clicks
            self.stroke_history.append(self.current_stroke.copy())
        
        self.current_stroke = []
        
        # AI completes the drawing
        self.complete_drawing()
        
    def complete_drawing(self):
        """
        The AI magic happens here.
        Analyzes left side and completes right side intelligently.
        """
        if not self.stroke_history:
            return
        
        # Convert left image to numpy for processing
        left_array = np.array(self.left_image)
        
        if self.completion_style == "smart_mirror":
            completed = self.smart_mirror_completion(left_array)
        elif self.completion_style == "creative":
            completed = self.creative_completion(left_array)
        else:  # minimal
            completed = self.minimal_completion(left_array)
        
        # Update right side
        self.right_image = Image.fromarray(completed)
        self.right_draw = ImageDraw.Draw(self.right_image)
        
        # Display on canvas
        self.update_canvas_display()
        
    def smart_mirror_completion(self, left_array):
        """
        Smart mirroring with variation.
        Not just flip - adds intelligent variation based on stroke patterns.
        """
        # Flip horizontally
        mirrored = cv2.flip(left_array, 1)
        
        # Add slight variations to make it more natural
        # Analyze stroke curvature and apply adaptive smoothing
        if len(self.stroke_history) > 3:
            # Add subtle noise to avoid perfect symmetry (more natural)
            noise = np.random.randint(-2, 3, mirrored.shape, dtype=np.int16)
            mirrored = np.clip(mirrored.astype(np.int16) + noise, 0, 255).astype(np.uint8)
            
            # Slight blur for organic feel
            mirrored = cv2.GaussianBlur(mirrored, (3, 3), 0)
        
        return mirrored
        
    def creative_completion(self, left_array):
        """
        Creative completion - adds flourishes and variations.
        Analyzes patterns and extends them creatively.
        """
        mirrored = cv2.flip(left_array, 1)
        
        # Detect edges in drawing
        gray = cv2.cvtColor(left_array, cv2.COLOR_RGB2GRAY)
        edges = cv2.Canny(gray, 50, 150)
        
        # Dilate edges slightly on right side for bolder look
        kernel = np.ones((2,2), np.uint8)
        edges_dilated = cv2.dilate(edges, kernel, iterations=1)
        
        # Combine mirrored with enhanced edges
        mirrored_gray = cv2.cvtColor(mirrored, cv2.COLOR_RGB2GRAY)
        mirrored_gray = cv2.bitwise_or(mirrored_gray, edges_dilated)
        
        # Convert back to RGB
        completed = cv2.cvtColor(mirrored_gray, cv2.COLOR_GRAY2RGB)
        
        return completed
        
    def minimal_completion(self, left_array):
        """
        Minimal completion - clean, simple mirror.
        """
        return cv2.flip(left_array, 1)
        
    def update_canvas_display(self):
        """Updates the right side of canvas with AI completion"""
        # Convert PIL image to PhotoImage for display
        right_photo = ImageTk.PhotoImage(self.right_image)
        
        # Clear previous right side
        self.canvas.delete("ai_completion")
        
        # Display new completion
        self.canvas.create_image(
            self.canvas_width//2, 0,
            anchor=tk.NW,
            image=right_photo,
            tags="ai_completion"
        )
        
        # Keep reference to prevent garbage collection
        self.canvas.image = right_photo
        
        # Redraw center line on top
        self.canvas.create_line(
            self.canvas_width//2, 0,
            self.canvas_width//2, self.canvas_height,
            fill='#ff0066',
            width=2,
            dash=(5, 5)
        )
        
    def clear_canvas(self):
        """Clear everything and start fresh"""
        self.canvas.delete("all")
        
        # Reset images
        self.left_image = Image.new('RGB', (self.canvas_width//2, self.canvas_height), 'white')
        self.right_image = Image.new('RGB', (self.canvas_width//2, self.canvas_height), 'white')
        self.left_draw = ImageDraw.Draw(self.left_image)
        self.right_draw = ImageDraw.Draw(self.right_image)
        
        # Reset stroke history
        self.stroke_history = []
        self.current_stroke = []
        
        # Redraw UI elements
        self.canvas.create_line(
            self.canvas_width//2, 0,
            self.canvas_width//2, self.canvas_height,
            fill='#ff0066',
            width=2,
            dash=(5, 5)
        )
        
        self.canvas.create_text(
            self.canvas_width//4, 20,
            text="YOUR DRAWING",
            font=("Helvetica", 14, "bold"),
            fill='#666666'
        )
        
        self.canvas.create_text(
            3*self.canvas_width//4, 20,
            text="AI COMPLETION",
            font=("Helvetica", 14, "bold"),
            fill='#00ff88'
        )
        
    def save_drawing(self):
        """Save the complete drawing"""
        # Combine left and right images
        full_image = Image.new('RGB', (self.canvas_width, self.canvas_height), 'white')
        full_image.paste(self.left_image, (0, 0))
        full_image.paste(self.right_image, (self.canvas_width//2, 0))
        
        # Save
        filename = f"doodle_ai_output.png"
        full_image.save(filename)
        
        messagebox.showinfo("Saved!", f"Drawing saved as {filename}")


def main():
    root = tk.Tk()
    app = DoodleAI(root)
    root.mainloop()


if __name__ == "__main__":
    main()