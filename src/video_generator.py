import sys
import random
from typing import Literal
import numpy as np
from moviepy.editor import *

from moviepy.editor import TextClip
from moviepy.config import change_settings
from moviepy.video.tools.segmenting import findObjects
from moviepy.video.io.VideoFileClip import VideoFileClip

if sys.platform != "linux":
    change_settings(
        {
            "IMAGEMAGICK_BINARY": r"C:\Program Files\ImageMagick-7.1.1-Q16-HDRI\magick.exe"
        }
    )


class TextAnimations:

    # Cascade function to animate from height 600 to 650
    def cascade(self, screenpos, i, nletters):

        cascade_duration = 3

        start_height = 500  # Starting height
        end_height = 550  # Ending height
        displacement = end_height - start_height
        v = np.array([0, displacement])  # Adjusted to move within the range

        # Adjust the speed and smoothness of the fall using a sine function
        d = lambda t: (
            0 if t < 0 else min(1, t / cascade_duration)
        )  # Animation duration controlled by cascade_duration
        return lambda t: screenpos + v * d(t - 0.15 * i)

    def bounce(self, screenpos, i, nletters):
        # Set random bounce height and speed for each letter
        bounce_height = random.randint(10, 30)
        bounce_speed = random.uniform(0.5, 1.5)
        start_time = random.uniform(0, 1)  # Randomize start time for each letter bounce

        def bouncing_letter(t):
            if t < start_time:
                return screenpos
            y_pos = screenpos[1] + bounce_height * np.sin(
                (t - start_time) * bounce_speed * 2 * np.pi
            )
            return (screenpos[0], y_pos)

        return bouncing_letter

    def wobble(self, screenpos, i, nletters):
        # Set wobble amplitude and speed for each letter
        wobble_amplitude = random.randint(5, 15)
        wobble_speed = random.uniform(0.5, 1.5)
        start_time = random.uniform(0, 1)  # Randomize start time for each letter wobble

        def wobbling_letter(t):
            if t < start_time:
                return screenpos
            x_pos = screenpos[0] + wobble_amplitude * np.sin(
                (t - start_time) * wobble_speed * 2 * np.pi
            )
            return (x_pos, screenpos[1])

        return wobbling_letter

    def spin(self, screenpos, i, nletters):
        center = np.array([300, 500])  # Define the center of spin
        angle = lambda t: (
            0 if t < 0 else 2 * np.pi * (t / 1.5)
        )  # Full spin in 1.5 seconds

        def pos(t):
            theta = angle(t)
            return center + np.array(
                [
                    200 * np.cos(theta + i * 2 * np.pi / nletters),
                    200 * np.sin(theta + i * 2 * np.pi / nletters),
                ]
            )

        return pos

    def roll(self, screenpos, i, nletters):
        start_x = screenpos[0]
        distance = 80  # Change this value to adjust the distance of the roll
        speed = 2  # Adjust this for faster or slower rolling

        def pos(t):
            x = start_x + distance * np.sin(speed * t)
            y = screenpos[1]
            return np.array([x, y])

        return pos

    def wave(self, screenpos, i, nletters):
        roll_duration = 3  # Duration of the rolling animation
        roll_repeats = 1  # Number of times the text rolls
        settle_height = 650  # Final resting position
        v = np.array([0, 100])  # Vertical rolling displacement

        d = lambda t: np.sin(2 * np.pi * roll_repeats * t / roll_duration) * (
            1 if t < roll_duration else 0
        )
        settle_pos = np.array([0, settle_height - screenpos[1]])
        return (
            lambda t: screenpos
            + v * d(t - 0.15 * i)
            + settle_pos * (1 - d(t - roll_duration))
        )

    def slot_machine_rajan(self, screenpos, i, nletters):
        roll_duration = 3  # Duration of the rolling animation
        roll_repeats = 2  # Number of times the text rolls
        settle_height = 650  # Final resting position
        v = np.array([0, 100])  # Vertical rolling displacement

        d = lambda t: np.sin(2 * np.pi * roll_repeats * t / roll_duration) * (
            1 if t < roll_duration else 0
        )
        settle_pos = np.array([0, settle_height - screenpos[1]])
        return (
            lambda t: screenpos
            + v * d(t - 0.15 * i)
            + settle_pos * (1 - d(t - roll_duration))
        )


class Animate(TextAnimations):

    def __init__(self, template_vid_pth: str) -> None:
        super().__init__()
        self.template_vid_pth = template_vid_pth
        self.template_video = self.__load_template()

    def __load_template(self):
        return VideoFileClip(self.template_vid_pth)

    def moveLetters(self, letters, funcpos):
        return [
            letter.set_pos(funcpos(letter.screenpos, i, len(letters)))
            for i, letter in enumerate(letters)
        ]

    def generate_bday_vid(
        self,
        kid_name: str,
        animation: Literal[
            "wobble", "roll", "cascade", "bounce", "wave", "slot_machine"
        ],
        fontsize: int = 140,
        font: str = "League-Spartan-Bold",
        color: str = "#FE6E6E",
    ):

        animation_mapp = {
            "wobble": self.wobble,
            "roll": self.roll,
            "cascade": self.cascade,
            "bounce": self.bounce,
            "wave": self.wave,
            "slot_machine": self.slot_machine_rajan,
        }
        txtClip = TextClip(
            txt=kid_name,
            fontsize=fontsize,
            font=font,
            color=color,
            bg_color="transparent",
        )

        ################
        video_width, video_height = self.template_video.size

        # Calculate text width and set it to center horizontally
        text_width, _ = txtClip.size  # Get the width of the text
        x_position = (video_width - text_width) / 2  # Center text horizontally
        y_position = 600  # Fixed vertical position for the text

        # Position the text clip in the center horizontally
        txtClip = txtClip.set_duration(self.template_video.duration).set_pos(
            (x_position, y_position)
        )

        # Composite the text clip on the video
        cvc = CompositeVideoClip([txtClip], size=(video_width, video_height))
        #################

        letters = findObjects(cvc)  # A list of ImageClips

        # Duration of animation effect
        animation_duration = (
            self.template_video.duration
        )  # Set animation duration as desired
        clips = [
            CompositeVideoClip(
                self.moveLetters(letters, funcpos), size=self.template_video.size
            ).subclip(0, animation_duration)
            for funcpos in [animation_mapp[animation]]
        ]

        # Concatenate clips and overlay on original self.template_video
        final_clip = concatenate_videoclips(clips)
        final_clip.set_duration(self.template_video.duration)

        final_video = CompositeVideoClip([self.template_video, final_clip])

        return final_video

        # final_video.write_videofile(
        #     f"animations/test/{ani.__name__}_{kid_name}.mp4",
        #     fps=25,
        #     codec="libx264",
        # )
