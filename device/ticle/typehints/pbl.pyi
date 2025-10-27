import ticle.ext as ext

class UltrasoicServoScanner:
    """
    A class to control a servo motor and an ultrasonic sensor for distance scanning.
    It sweeps the servo motor across a specified range and takes distance readings at each angle.
    The best angle with the minimum distance is returned.
    """
    
    def __init__(self, servo:object, sonic:object, step:int=2, settle_ms:int=20, samples:int=5):
        """
        :param servo: ServoMotor object
        :param sonic: Ultrasonic object 
        :param step: int, angle step for servo motor
        :param settle_ms: int, time to wait for servo to settle in ms
        :param samples: int, number of samples to take for each angle
        """


    def sweep(self, start:int=0, end:int=180) -> dict: 
        """
        Sweep the servo motor from start to end angle and return the best angle with minimum distance.
        :param start: int, starting angle
        :param end: int, ending angle
        :return: dict, best angle and distance
        """


class WS2812Matrix_Effect:
    def __init__(self, ws:ext.WS2812Matrix):
        """
        A class to apply various effects on a WS2812 LED matrix.
        It provides methods to create effects like sparkle, meteor rain, plasma, fireworks, campfire, and wave RGB.
        
        :param ws: WS2812Matrix object, the LED matrix to apply effects on
        """

    def stop(self):
        """
        Stop the current effect and reset the effect ID.
        """

    def sparkle(self, *, base=(0,0,0), sparkle_color=(255,255,255), density=0.1, decay=0.9, speed=0.03):
        """
        Create a sparkle effect on the LED matrix.
        
        :param base: tuple, RGB color for the base color of the matrix
        :param sparkle_color: tuple, RGB color for the sparkle
        :param density: float, density of the sparkles (0-1)
        :param decay: float, decay factor for the sparkle brightness (0-1)
        :param speed: float, speed of the effect in seconds
        """

    def meteor_rain(self, *, colors=((255,0,0),(0,0,255)), count=3, decay=0.8, speed=0.04):
        """
        Create a meteor rain effect on the LED matrix.
        
        :param colors: tuple, list of RGB colors for the meteors
        :param count: int, number of meteors to create
        :param decay: float, decay factor for the meteor brightness (0-1)
        :param speed: float, speed of the effect in seconds
        """

    def plasma(self, *, hue_shift=2, speed=0.05):
        """
        Create a plasma effect on the LED matrix.
        
        :param hue_shift: int, the shift in hue for the plasma effect
        :param speed: float, speed of the effect in seconds
        """

    def fireworks(self, *, sparks=24, fade=0.9, speed=0.03, colors=((255,128,0),(255,255,255),(0,255,255))):
        """
        Create a fireworks effect on the LED matrix.
        
        :param sparks: int, number of sparks in the fireworks
        :param fade: float, fade factor for the sparks (0-1)
        :param speed: float, speed of the effect in seconds
        :param colors: tuple, list of RGB colors for the sparks
        """

    def campfire(self, *, cooling=55, sparking=120, speed=0.03):
        """
        Create a campfire effect on the LED matrix.
        
        :param cooling: int, cooling factor for the heat (0-255)
        :param sparking: int, sparking factor for the heat (0-255)
        :param speed: float, speed of the effect in seconds
        """

    def wave_rgb(self, *, speed=0.1):
        """
        Create a wave RGB effect on the LED matrix.
        
        :param speed: float, speed of the effect in seconds
        """


class BtAudioAmp:
    SHOT_HOLD = 50
    LONG_HOLD = 1300
    
    def __init__(self, mode, scan, down, up, shot_hold_ms=SHOT_HOLD, long_hold_ms=LONG_HOLD):
        """
        Bluetooth Audio Amplifier Control
        
        :param mode: pin number for mode control
        :param scan: pin number for scan control
        :param down: pin number for down/previous control
        :param upn: pin number for up/next control
        """        
        
    def __press(self, pin, hold_ms):
        """
        Press a button for a specified duration.
        :param pin: Pin to press
        :param hold_ms: Duration to press the button in milliseconds
        """

    def down(self):
        """
        Press the down/previous button for a specified duration.
        """

    def up(self):
        """
        Press the up/next button for a specified duration.
        """

    def prev(self):   
        """
        Press the down/previous button for a specified duration.
        """

    def next(self):
        """
        Press the up/next button for a specified duration.
        """

    def pause_resume(self):
        """
        Press the mode button for a specified duration.
        :param duration: Duration to press the button in milliseconds
        """
