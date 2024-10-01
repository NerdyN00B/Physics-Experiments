# Python Webcam Software
This software is originally written by Benjamin van Ommen in 2019. The application can read out a webcam (tested only with the webcams in the bachelor lab), display its output live, shows the mean intensity (calculated using the mean rgb colour where `(255,255,255)` is a white screen, `(0,0,0)` is black)
of each column of pixels and allows saving the displayed data to disk.

The webcam supports a the following resolution modes:
 - 1280x1024 @ 9 fps and 5 fps (used in this program);
 - 640x480 @ 30,25,20,15,10,5 fps;
 - 352x288 @ 30,25,20,15,10,5 fps;

There are also some lower resolution modes, however this will only throw away information; modern hardware can easily handle 640x480 at 30 fps, or downsample is on the CPU. The webcam will autonomously choose a framerate depending on the lighting. If it is overexposed it will switch to a higher framerate, and vice-versa. I could find no way to choose the framerate/exposure time of the webcam, however it may be possible to do this nevertheless. It might be a good idea to look for another
way to control the webcam, by using a different python library or using a library in C.

The used way of controlling the webcam is as follows:
 - I use the opencv library, which has python bindings (opencv actually runs on C, however you can call the C functions from python and continue with the outputs from these functions in python) provided by opencv-python.
 - opencv-python can be imported by "import cv2".
Doing measurements is very straightforward: 
 - create a VideoCapture object using cv2.VideoCapture(0) (or another index if multiple cams are connected)
 - To then get a frame from the webcam, use the read() method of your VideoCapture object. This will return an rval and a frame.
 - The `rval` is `True` if the measurement was succesful, and `False` otherwise. The `frame` is a numpy array with shape 1280x1024x3 in our case. It contains for each pixel an `r`, `g` and `b` colour which ranges from `0` to `255`.

When you are done measuring, remember to use the release() method to allow the webcam to be used by other programmes. If you have more questions I recommend you look at the python code to see the above in action. If you have further questions don't hesitate to contact me: please ask Paul Logman (or whoever has replaced him, if you live in the far future) for my email. 


