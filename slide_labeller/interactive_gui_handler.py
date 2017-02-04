import Tkinter
from Tkinter import *

import PIL
from PIL import Image, ImageTk

import cv2

import h5py

import numpy as np

class InteractiveGUI(object):

    """
    Our class for an interactive gui for LIRA Live.
    """
    def __init__(self, classifications, colors, sub_h, sub_w, alpha, dual_monitor):
        """
        Our main image, and main predictions that we are currently working with. 
        """
        self.np_img = np.array([-1])
        self.predictions = np.array([-1])

        """
        Metadata for reference here
        """
        self.classifications = classifications
        self.colors = colors
        self.sub_h = sub_h
        self.sub_w = sub_w

        """
        Metadata variables to use after closing our session.
        """
        self.alpha = alpha

        """
        Indicator / Flag values for the status of the session, 
            so that our main file can know when to:
            refresh the current image with new parameters,
            get the next image, 
            or quit the session and move on,
            respectively.
        """
        self.flag_refresh = False
        self.flag_next = False
        self.flag_quit = False

        """
        Variables to store the location where we opened our bulk select rectangle
        """
        self.bulk_select_initial_x = 0
        self.bulk_select_initial_y = 0

        """
        Variables for storing the indices in our predictions matrix for
            the predictions we currently have selected to update.
        """
        self.selected_prediction_i_x1 = 0
        self.selected_prediction_i_y1 = 0
        self.selected_prediction_i_x2 = 0
        self.selected_prediction_i_y2 = 0

        """
        For configuring the window
        """
        self.main_canvas_percentage = 0.90
        self.tool_canvas_percentage = 1-self.main_canvas_percentage
        self.screen_height_padding_percentage = 0.20
        if dual_monitor:
            self.screen_width_padding_percentage = 0.52
        else:
            self.screen_width_padding_percentage = 0.02

    def get_relative_coordinates(self, event):
        """
        Given an event with an x and y coordinate, return the coordinates relative to their parent widget/canvas.
        """
        canvas = event.widget
        return canvas.canvasx(event.x), canvas.canvasy(event.y)

    def get_rectangle_coordinates(self, x1, y1, x2, y2):
        """
        Given two sets of coordinates defining a rectangle between them,
            return two sets of coordinates for the top-left and bottom-right corner of the rectangle,
            respectively

        We do this by simply handling each possible orientation of the points relative to each other,
            and returning the correct combination of the points
        """
        if x1 <= x2 and y1 <= y2:
            """
            1
             \
              2
            """
            return x1, y1, x2, y2

        elif x1 > x2 and y1 <= y2:
            """
              1
             /
            2 
            """
            return x2, y1, x1, y2
        elif x1 <= x2 and y1 > y2:
            """
              2
             /
            1 
            """
            return x1, y2, x2, y1

        elif x1 > x2 and y1 > y2:
            """
            2
             \
              1
            """
            return x2, y2, x1, y1
    def get_outline_rectangle_coordinates(self, rect_x1, rect_y1, rect_x2, rect_y2, sub_h, sub_w):
        """
        Given two pairs of coordinates for the top left and bottom right corners of a rectangle,
            as well as our subsection height and width,
        We return two new pairs of coordinates for a new rectangle, 
            which outlines all the subsections the given rectangle encompasses.

        Luckily, this is easily done with a simple modular arithmetic formula I made up.
        """
        outline_rect_x1 = np.floor(rect_x1/sub_w)*sub_w
        outline_rect_y1 = np.floor(rect_y1/sub_h)*sub_h
        outline_rect_x2 = np.ceil(rect_x2/sub_w)*sub_w
        outline_rect_y2 = np.ceil(rect_y2/sub_h)*sub_h

        return outline_rect_x1, outline_rect_y1, outline_rect_x2, outline_rect_y2

    def mouse_left_click(self, event):
        """
        Handler for when the left click is pressed
        """
        """
        This function / event listener starts our bulk select rectangle for the user to select multiple classifications at once.

        We clear our previously made bulk select outline rectangle, and then:

        Since we've just pressed down the button, we store the relative coordinates into our class variables for future events 
            to use in computing where to display the rectangle.
        """
        print "Left Mouse clicked, opening bulk select rectangle..."
        canvas = event.widget 
        canvas.delete("outline_rect")
        self.bulk_select_initial_x, self.bulk_select_initial_y = self.get_relative_coordinates(event)

    def mouse_left_move(self, event):
        """
        Handler for when the left click is moved while pressed
        """
        """
        First, we get the relative coordinates given our event.
        """
        rel_x, rel_y = self.get_relative_coordinates(event)

        canvas = event.widget
        """
        Then, we update our rectangle to be drawn from our initial x and y coordinates to our current x and y coordinates.
        Our create_rectangle method requires the top left point's coordinates, then the bottom right's coordinates.
            Since we don't always have these points, we just have two points that are diagonally opposite, 
                we compute the necessary coordinates with our get_rectangle_coordinates() function.
            Then, we delete any existing rectangles, and
            we create a new rectangle with a red outline and a tag so we can delete it whenever we need to.
        """
        rect_x1, rect_y1, rect_x2, rect_y2 = self.get_rectangle_coordinates(self.bulk_select_initial_x, self.bulk_select_initial_y, rel_x, rel_y)
        canvas.delete("bulk_select_rect")
        canvas.create_rectangle(rect_x1, rect_y1, rect_x2, rect_y2, fill='', outline="red", width=3, tags="bulk_select_rect")

    def mouse_left_release(self, event):
        """
        Handler for when the left click is released
        """
        """
        We get the relative coordinates given our event.
        """
        print "Left Mouse released, selecting subsections inside bulk select rectangle..."
        canvas = event.widget

        rel_x, rel_y = self.get_relative_coordinates(event)

        """
        Now we need to find the subsections that our rectangle encompasses,
            so we need to find the top left and bottom right corners again.
        """
        rect_x1, rect_y1, rect_x2, rect_y2 = self.get_rectangle_coordinates(self.bulk_select_initial_x, self.bulk_select_initial_y, rel_x, rel_y)

        """
        Using these, we get new coordinates that outline all the subsections that our bulk select rectangle encompasses.
        """
        outline_rect_x1, outline_rect_y1, outline_rect_x2, outline_rect_y2 = self.get_outline_rectangle_coordinates(rect_x1, rect_y1, rect_x2, rect_y2, self.sub_h, self.sub_w)

        """
        Then we delete our bulk select rectangle, now that we have the subsections it encompassed.
        """
        canvas.delete("bulk_select_rect")

        """
        And we draw our new outline rectangle.
        """
        canvas.create_rectangle(outline_rect_x1, outline_rect_y1, outline_rect_x2, outline_rect_y2, fill='', outline="darkRed", width=3, tags="outline_rect")

        """
        Then, using our outline rectangle coordinates, 
            we get the indices for our predictions matrix,
            so that we can modify all the predictions in our selected area accordingly once a classification is selected.
        """
        self.selected_prediction_i_x1 = int(outline_rect_x1/self.sub_w)
        self.selected_prediction_i_y1 = int(outline_rect_y1/self.sub_h)
        self.selected_prediction_i_x2 = int(outline_rect_x2/self.sub_w)
        self.selected_prediction_i_y2 = int(outline_rect_y2/self.sub_h)

    def key_press(self, event):
        """
        Handler for when a key is pressed. 
        Depending on the key pressed, we may either:
            1. classify the currently bulk-selected section if we have selected a classification keyboard shortcut,
            2. call another event handler if we call a command shortcut, or
            3. we may do nothing if we have not selected a classification keyboard shortcut

        So we first check if the key pressed is one of our classification keyboard shortcut keys
            by checking if it is a number key within the range of 1-len(classifications) (inclusive)
        """
        canvas = event.widget
        c = event.char
        print "%s pressed..." % c
        try:
            key_num = int(c)

            if (1 <= key_num and key_num <= len(self.classifications)):
                print "Classifying selected section..."
                """
                If so, now we subtract 1 to get the classification index
                """
                classification_i = key_num-1

                """
                And now we re-assign all the values in our predictions matrix within the ranges specified by our bulk-select rectangle.
                """
                self.predictions[self.selected_prediction_i_y1:self.selected_prediction_i_y2, self.selected_prediction_i_x1:self.selected_prediction_i_x2] = classification_i

                """
                Then we delete our bulk select outline rectangle and return
                """
                canvas.delete("outline_rect")
                return
        except:
            """
            If it wasn't a number, then we check if it is another keybind.
            """
            c = c.upper()
            if c == 'R':
                """
                Our refresh keybind, call the associated button handler.
                """
                self.refresh_session_button_press()

            elif c == 'N':
                """
                Our next keybind, call the associated button handler.
                """
                self.next_img_button_press()

            elif c == 'Q':
                """
                Our quit keybind, call the associated button handler.
                """
                self.quit_session_button_press()

            """
            Whatever happens, we are done with this now.
            """
            return


    def refresh_session_button_press(self):
        """
        Handler for when the REFRESH IMAGE button is pressed
        """
        print "Refreshing / Reloading session..."

        """
        We update our class variable to match whatever values we have changed during the session
        """
        self.alpha = self.alpha_slider.get()

        """
        We destroy our window and change flag
        """
        self.window.destroy()
        self.flag_refresh = True
        
    def next_img_button_press(self):
        """
        Handler for when the NEXT IMAGE button is pressed
        """
        print "Going to next image..."

        """
        We update our class variable to match whatever values we have changed during the session
        """
        self.alpha = self.alpha_slider.get()

        """
        We destroy our window and change flag
        """
        self.window.destroy()
        self.flag_next = True

    def quit_session_button_press(self):
        """
        Handler for when the QUIT SESSION button is pressed
        """
        print "Ending session..."

        """
        We update our class variable to match whatever values we have changed during the session
        """
        self.alpha = self.alpha_slider.get()

        """
        Then we destroy our window and change flag
        """
        self.window.destroy()
        self.flag_quit = True

    @staticmethod
    def get_relative_canvas_dimensions(screen_width, screen_height, main_canvas_percentage, tool_canvas_percentage, screen_width_padding_percentage, screen_height_padding_percentage, relative_dim):
        """
        Given our percentage for main canvas's size and tool canvas's size, as well as the padding for any canvas and the dimension to divide into portions,
            we return the height and width dimensions for both main and tool canvas.
        """
        """
        First, pad both the necessary screen padding amount.
        """
        screen_width = screen_width - screen_width_padding_percentage*screen_width
        screen_height = screen_height - screen_height_padding_percentage*screen_height

        """
        Then invert these percentages so we don't give the opposite of what we want in our upcoming calculations
        """
        main_canvas_percentage = 1-main_canvas_percentage
        tool_canvas_percentage = 1-tool_canvas_percentage

        """
        Then we give each section it's corresponding percentage of the padded screen width.
        """
        if relative_dim == "w":
            """
            Compute the relative width of each
            """
            main_canvas_width = screen_width - main_canvas_percentage*screen_width
            tool_canvas_width = screen_width - tool_canvas_percentage*screen_width

            """
            And assign them the full height
            """
            main_canvas_height = screen_height
            tool_canvas_height = screen_height

        elif relative_dim == "h":
            """
            Compute the height of each
            """
            main_canvas_height = screen_height - main_canvas_percentage*screen_height
            tool_canvas_height = screen_height - tool_canvas_percentage*screen_height

            """
            And assign them the full width
            """
            main_canvas_width = screen_width
            tool_canvas_width = screen_width

        else:
            sys.exit("Incorrect relative_dim parameter input for get_relative_canvas_dimensions()")

        return main_canvas_width, main_canvas_height, tool_canvas_width, tool_canvas_height

    def start_interactive_session(self):
        """
        Check if we have an image to display and predictions to update, otherwise exit.
        """
        if np.all(self.np_img==-1) or np.all(self.predictions == -1):
            sys.exit("Error: You must assign an image to display and predictions to update before starting an interactive GUI session!")

        """
        Open our main Tkinter window 
        """
        self.window = Tk()

        """
        Get our screen width and height, and assign portions to each of our two main canvases respective of the percentage of the screen we want to give them.
        """
        screen_width = self.window.winfo_screenwidth()
        screen_height = self.window.winfo_screenheight()

        main_canvas_width, main_canvas_height, tool_canvas_width, tool_canvas_height = self.get_relative_canvas_dimensions(
                screen_width, 
                screen_height, 
                self.main_canvas_percentage,
                self.tool_canvas_percentage,
                self.screen_width_padding_percentage,
                self.screen_height_padding_percentage,
                relative_dim="w")

        """
        First convert our np array from BGR to RGB
        """
        self.np_img = cv2.cvtColor(self.np_img, cv2.COLOR_BGR2RGB)

        """
        Convert our image from numpy array, to PIL image, then to Tkinter image.
        """
        img = ImageTk.PhotoImage(Image.fromarray(self.np_img))

        """
        Initialize our main frame
        """
        frame = Frame(self.window, bd=5, relief=SUNKEN)
        frame.grid(row=0,column=0)

        """
        Initialize our main canvas with the majority of our screen, and the scroll region as the size of our image,
        and Initialize our tool canvas with a small portion of the bottom of our screen
        """
        main_canvas=Canvas(frame, bg='#000000', width=main_canvas_width, height=main_canvas_height, scrollregion=(0,0,self.np_img.shape[1],self.np_img.shape[0]))
        tool_canvas=Canvas(frame, width=tool_canvas_width, height=tool_canvas_height, scrollregion=(0,screen_height,self.np_img.shape[1],0))

        """
        Initialize horizontal and vertical scrollbars on main canvas
        """
        hbar=Scrollbar(frame,orient=HORIZONTAL)
        hbar.pack(side=BOTTOM,fill=X)
        hbar.config(command=main_canvas.xview)
        vbar=Scrollbar(frame,orient=VERTICAL)
        vbar.pack(side=RIGHT,fill=Y)
        vbar.config(command=main_canvas.yview)
        main_canvas.config(xscrollcommand=hbar.set, yscrollcommand=vbar.set)

        """
        Add our image to the main canvas, in the upper left corner.
        """
        main_canvas.create_image(0, 0, image=img, anchor="nw")

        """
        Add our various UI tools to our tool canvas
        """
        """
        Initialize our slider to change the alpha transparency
        """
        self.alpha_slider = Scale(tool_canvas, from_=0, to=1, resolution=0.01, length=tool_canvas_width, orient=HORIZONTAL, label="Alpha / Overlay Transparency")
        self.alpha_slider.set(self.alpha)
        self.alpha_slider.pack()

        """
        Generate a header for our classifications, then display them with a color key
        """
        classification_header = Label(tool_canvas, text="\nClassification Key") 
        classification_header.pack(fill=X)

        for i, (classification, color) in enumerate(zip(self.classifications, self.colors)):
            """
            Since our colors are in BGR, and tkinter only accepts hex, we have to create a hex string for them, in RGB order.
            """
            b, g, r = color
            hex_color_str = "#%02x%02x%02x" % (r, g, b)
            
            """
            We then check get the color's brightness using the relative luminance algorithm
                https://en.wikipedia.org/wiki/Relative_luminance
            """
            color_brightness = (0.2126*r + 0.7152*g + 0.0722*b)/255;
            if color_brightness < 0.5:
                """
                Dark color, bright font.
                """
                text_color = "white"
            else:
                """
                Bright color, dark font.
                """
                text_color = "black"
            
            """
            Then we generate our label string to include the keyboard shortcut for this classification
            """
            label_str = "Key %i: %s" % (i+1, classification)
            color_label = Label(tool_canvas, text=label_str, bg=hex_color_str, fg=text_color, anchor="w")
            color_label.pack(fill=X)
        
        """
        Add our buttons for refreshing, going to the next image, and quitting, respectively.
        """
        refresh_session_button = Button(tool_canvas, text="REFRESH SESSION", bg="#0000ff", fg="white", highlightcolor="#0000ff", activebackground="#0000ff", activeforeground="white",command=self.refresh_session_button_press)
        next_img_button = Button(tool_canvas, text="NEXT IMAGE", bg="#00ff00", fg="black", highlightcolor="#00ff00", activebackground="#00ff00",activeforeground="black", command=self.next_img_button_press)
        quit_session_button = Button(tool_canvas, text="QUIT SESSION", bg="#ff0000", fg="white", highlightcolor="#ff0000", activebackground="#ff0000", activeforeground="white", command=self.quit_session_button_press)

        refresh_session_button.pack(fill=X, pady=(30, 5))
        next_img_button.pack(fill=X, pady=(5,5))
        quit_session_button.pack(fill=X, pady=(5,5))

        """
        Add our event listeners to the main canvas
        """
        main_canvas.focus_set()

        """
        Handler for when the left click is pressed
        """
        main_canvas.bind("<Button 1>", self.mouse_left_click)

        """
        Handler for when the left click is moved while pressed
        """
        main_canvas.bind("<B1-Motion>", self.mouse_left_move)

        """
        Handler for when the left click is released
        """
        main_canvas.bind("<ButtonRelease-1>", self.mouse_left_release)

        """
        Handler for when any key is pressed
        """
        main_canvas.bind("<Key>", self.key_press)

        """
        Open our canvases in the main window.
        """
        main_canvas.pack(side=LEFT)
        tool_canvas.pack(side=RIGHT)

        """
        Initialize main window and main loop.
        """
        self.window.mainloop()