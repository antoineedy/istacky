# Do the necessary imports

from PIL import Image, ImageColor
import numpy as np
import ipywidgets as widgets
import cv2
import pandas as pd
import time
from copy import deepcopy
from ipyfilechooser import FileChooser
from IPython.display import display

# Create the class


class BlendedImage:
    def __init__(
        self,
        background: Image.Image or np.array,
        images,
        positions=None,
        opacities=None,
        background_resize=None,
        image_scales=None,
        remove=None,
        cropped=None,
        images_crop=None,
        code=None,
    ):
        """
        Blend images on a background.

        Parameters
        ----------
        background : PIL.Image.Image or numpy.ndarray
            Background image.
        images : PIL.Image.Image or numpy.ndarray or list
            Image to superpose.
        positions : tuple or list or None
            Position of the image on the background.
        opacities : float or list or None
            Opacity of the image.
        background_resize : float
            Coefficient to resize the background.
        image_scales : float or list or None
            Height of the images in percentage of the background height.
        remove : list or None
            Remove specific color from the image.
        cropped : list or None
            Crop or expand the background.
        images_crop : list or None
            Crop the images.
        code : str or None
            Code to reproduce a previously created blended image.
        """
        if not isinstance(images, list):
            images = [images]

        if positions is None:
            positions = [(0, 0)] * len(images)
        elif not isinstance(positions, list):
            positions = [positions]
        if opacities is None:
            opacities = [1] * len(images)
        if image_scales is None:
            image_scales = [0.5] * len(images)
        if remove is None:
            remove = [[False, [255, 255, 255], 0] for i in range(len(images))]
        to_show = [True] * len(images)
        if cropped is None:
            cropped = [0, 0, 0, 0]
        if images_crop is None:
            images_crop = [[0, 0, 0, 0] for i in range(len(images))]

        self.__last_size = None

        if code is not None:
            if not isinstance(code, str):
                raise TypeError("code must be str")
            code = code.split("s")
            self.__last_size = code[1].split(",")
            self.__last_size = [
                int(self.__last_size[i]) for i in range(len(self.__last_size) - 1)
            ]
            code = code[0]
            code = code.split("c")
            cropped = code[1].split(",")
            cropped = [int(cropped[i]) for i in range(len(cropped))]
            code = code[0]
            code = code.split("#")
            code = code[1:]
            for k in range(len(code)):
                code[k] = code[k].split("-")

            if len(code) != len(images):
                raise ValueError(
                    "code must have the same number of images as the number of images given"
                )

            positions = []
            opacities = []
            image_scales = []
            remove = []
            to_show = []
            images_crop = []
            for k in range(len(code)):
                image_scales.append(float(code[k][0]))
                positions.append((int(code[k][1]), int(code[k][2])))
                opacities.append(float(code[k][3]))
                the_color = code[k][5].split(",")
                the_color = [int(the_color[i]) for i in range(len(the_color))]
                remove.append(
                    [True if code[k][4] == "1" else False, the_color, int(code[k][6])]
                )
                to_show.append(True if int(code[k][7]) == 1 else False)
                the_cropping = code[k][8].split(",")
                images_crop.append(
                    [int(the_cropping[i]) for i in range(len(the_cropping))]
                )

        self.__background = background
        self.__images = images

        if isinstance(background, Image.Image):
            background = background.convert("RGB")
            self.__background = np.array(background)
        elif not isinstance(background, np.array):
            raise TypeError(
                "self.__background must be PIL.Image.Image or numpy.ndarray"
            )

        stored_images = []

        for image in images:
            if isinstance(image, Image.Image):
                image = image.convert("RGB")
                stored_images.append(np.array(image))
            elif not isinstance(image, np.array):
                raise TypeError("image must be PIL.Image.Image or numpy.ndarray")

        self.__images = stored_images

        self.__positions = positions
        self.__opacities = opacities
        self.__background_resize = background_resize
        self.__image_scales = image_scales
        # remove = [True or False, Color, Threshold]
        self.__remove = deepcopy(remove)
        self.__to_show = to_show
        self.__background_display_height = 350
        self.__background_display_width = int(
            self.__background_display_height
            * (self.__background.shape[1] / self.__background.shape[0])
        )

        self.__image_heights = list(
            np.array(self.__image_scales) * self.__background.shape[0]
        )
        self.__image_widths = []
        k = 0
        for image in self.__images:
            height = image.shape[1] * (self.__image_heights[k] / image.shape[0])
            self.__image_widths.append(height)
            k += 1

        self.__visualize_layer = False

        self.__cropped = cropped
        self.__background_croped = None
        self.__images_crop = images_crop
        self.__update_background_crop()

        if self.__last_size is not None:
            for k in range(len(positions)):
                positions[k] = (
                    int(
                        positions[k][0]
                        * self.__background_croped.shape[1]
                        / self.__last_size[1]
                    ),
                    int(
                        positions[k][1]
                        * self.__background_croped.shape[0]
                        / self.__last_size[0]
                    ),
                )

        self.__create_image()
        self.__update_code()

    def show(self):
        """
        Show the blended image in a Jupyter Notebook.

        Returns
        -------
            None
        """
        display(Image.fromarray(self.__result))

    def get_code(self):
        """
        Get the code to reproduce the blended image.

        Returns
        -------
        str
            Code to reproduce the blended image.
        """
        return self.__code

    def to_image(self):
        """
        Return the blended image as a PIL.Image.Image.

        Returns
        -------
        PIL.Image.Image
            Blended image.
        """
        return Image.fromarray(self.__result)

    def to_array(self):
        """
        Return the blended image as a numpy.ndarray.

        Returns
        -------
        numpy.ndarray
            Blended image.
        """
        return self.__result

    def __update_code(self):
        """
        Update the code.
        """
        self.__code = ""
        for k in range(len(self.__images)):
            self.__code += (
                "#"
                + str(round(self.__image_scales[k], 4))
                + "-"
                + str(int(self.__positions[k][0]))
                + "-"
                + str(int(self.__positions[k][1]))
                + "-"
                + str(round(self.__opacities[k], 4))
                + "-"
                + str(1 if self.__remove[k][0] else 0)
                + "-"
                + str(self.__remove[k][1])[1:-1].replace(" ", "")
                + "-"
                + str(self.__remove[k][2])
                + "-"
                + str(1 if self.__to_show[k] else 0)
                + "-"
                + str(self.__images_crop[k])[1:-1].replace(" ", "")
            )
        self.__code += "c" + str(self.__cropped)[1:-1].replace(" ", "")
        # shape with crop
        theshape = self.__background_croped.shape
        # theshape = self.__background.shape
        self.__code += "s" + str(theshape)[1:-1].replace(" ", "")

    def __change_image_scale(self, change, k):
        """
        Change the image scale.
        """
        self.__image_scales[k] = change
        self.__image_heights[k] = (
            self.__image_scales[k] * self.__background_croped.shape[0]
        )
        self.__image_widths[k] = self.__images[k].shape[1] * (
            self.__image_heights[k] / self.__images[k].shape[0]
        )
        self.__update_code()

    def __blend_arrays(self, background, image, opacity, remove, position, image_crop):
        """
        Blend two arrays with opacity.

        Parameters
        ----------
        background : numpy.ndarray
            Background image.
        image : numpy.ndarray
            Image to superpose.
        opacity : float
            Opacity of the image.

        Returns
        -------
        numpy.ndarray
            Superposed image.
        """

        # image crop is in percent, put it in pixels
        image_crop = [int(image_crop[i] * image.shape[i % 2] / 100) for i in range(4)]

        image = image[
            image_crop[0] : image.shape[0] - image_crop[2],
            image_crop[3] : image.shape[1] - image_crop[1],
            :,
        ]

        if position[0] < 0:
            image = image[:, -position[0] :, :]
            position = (0, position[1])
        if position[1] < 0:
            image = image[-position[1] :, :, :]
            position = (position[0], 0)
        if position[0] + image.shape[1] > background.shape[1]:
            image = image[:, : background.shape[1] - position[0], :]
        if position[1] + image.shape[0] > background.shape[0]:
            image = image[: background.shape[0] - position[1], :, :]

        mask = np.zeros(background.shape)

        # if remove[0]:
        #     mask = image.copy()
        #     mask[image > 240] = 1
        #     mask[mask != 1] = 0
        #     mask = mask.astype(np.uint8)

        isImage = True
        if image.shape[0] == 0 or image.shape[1] == 0:
            isImage = False

        if remove[0] and isImage:
            color = remove[1]
            threshold = remove[2]
            lower = np.array(
                [color[0] - threshold, color[1] - threshold, color[2] - threshold]
            )
            upper = np.array(
                [color[0] + threshold, color[1] + threshold, color[2] + threshold]
            )
            mask = cv2.inRange(image, lower, upper)
            mask = cv2.bitwise_not(mask)
            mask = cv2.cvtColor(mask, cv2.COLOR_GRAY2RGB)
            mask = np.array(mask) - 255

        image = image * opacity + background[
            position[1] : position[1] + image.shape[0],
            position[0] : position[0] + image.shape[1],
            :,
        ] * (1 - opacity)

        if remove[0] and isImage:
            # if pixel in mask, then pixel comes form background, else from image
            image[mask == 1] = background[
                position[1] : position[1] + image.shape[0],
                position[0] : position[0] + image.shape[1],
                :,
            ][mask == 1]

        # out is image starting at position and background
        out = background.copy()
        out[
            position[1] : position[1] + image.shape[0],
            position[0] : position[0] + image.shape[1],
            :,
        ] = image.copy()

        return out

    def __update_background_crop(self):
        """
        Update the background crop.
        """
        the_back = self.__background.copy()
        the_back = Image.fromarray(the_back)
        the_back = the_back.crop(
            (
                self.__cropped[3],
                self.__cropped[0],
                the_back.width - self.__cropped[1],
                the_back.height - self.__cropped[2],
            )
        )
        # changing the background to white
        the_back = np.array(the_back)
        # left side
        the_back[:, : -self.__cropped[3], :] = [255, 255, 255]
        # right side
        the_back[:, the_back.shape[1] + self.__cropped[1] :, :] = [255, 255, 255]
        # top side
        the_back[: -self.__cropped[0], :, :] = [255, 255, 255]
        # bottom side
        the_back[the_back.shape[0] + self.__cropped[2] :, :, :] = [255, 255, 255]

        self.__background_croped = np.array(the_back)

    def __create_image(self):
        """
        Superpose image on background at position with opacity.

        Parameters
        ----------
        background : PIL.Image.Image or numpy.ndarray
            Background image.
        image : PIL.Image.Image or numpy.ndarray
            Image to superpose.
        position : tuple
            Position of the image on the background.
        opacity : float
            Opacity of the image.
        background_background_resize : float
            Coefficient to resize the background.
        image_height : float
            Height of the image in percentage of the background height.

        Returns
        -------
        numpy.ndarray
            Superposed image.
        """

        background = self.__background_croped.copy()
        images = self.__images.copy()

        # resize self.__background_croped
        if self.__background_resize is not None:
            background = Image.fromarray(background)
            background = background.resize(
                (
                    int(background.width * self.__background_resize),
                    int(background.height * self.__background_resize),
                )
            )
            background = np.array(self.__background_croped)

        for k in range(len(images)):
            image = images[k]
            image = Image.fromarray(image)
            new_height = background.shape[0] * self.__image_scales[k]
            new_width = image.width * (new_height / image.height)
            image = image.resize((int(new_width), int(new_height)))
            image = np.array(image)
            images[k] = image

        # blend the background part and the image
        for k in range(len(self.__images))[::-1]:
            if not self.__to_show[k]:
                continue
            background = self.__blend_arrays(
                background,
                images[k],
                self.__opacities[k],
                self.__remove[k],
                self.__positions[k],
                self.__images_crop[k],
            )

        background_to_display = background.copy()
        background_to_display = Image.fromarray(background_to_display)
        background_to_display = background_to_display.convert("RGBA")
        background_to_display = background_to_display.resize(
            (
                self.__background_display_width,
                self.__background_display_height,
            )
        )
        background_to_display = background_to_display.convert("RGB")
        background_to_display = np.array(background_to_display)

        # check if exist
        try:
            self.__tab
        except AttributeError:
            self.__tab = None

        if self.__visualize_layer and self.__tab is not None:
            k = self.__tab.selected_index
            if k == len(self.__images):
                pass
            else:
                # put red rectangle on selected image
                image_crop = [int(self.__images_crop[k][i]) for i in range(4)]
                # now in pixel (it was in percent):
                image_crop[0] = image_crop[0] * self.__image_heights[k] / 100
                image_crop[2] = image_crop[2] * self.__image_heights[k] / 100
                image_crop[1] = image_crop[1] * self.__image_widths[k] / 100
                image_crop[3] = image_crop[3] * self.__image_widths[k] / 100
                rectangle_position = [
                    self.__positions[k][0],
                    self.__positions[k][1],
                    self.__positions[k][0]
                    + self.__image_widths[k]
                    - image_crop[1]
                    - image_crop[3],
                    self.__positions[k][1]
                    + self.__image_heights[k]
                    - image_crop[0]
                    - image_crop[2],
                ]
                rectangle_position[0] = (
                    rectangle_position[0]
                    * self.__background_display_width
                    / self.__background_croped.shape[1]
                )
                rectangle_position[1] = (
                    rectangle_position[1]
                    * self.__background_display_height
                    / self.__background_croped.shape[0]
                )
                rectangle_position[2] = (
                    rectangle_position[2]
                    * self.__background_display_width
                    / self.__background_croped.shape[1]
                )
                rectangle_position[3] = (
                    rectangle_position[3]
                    * self.__background_display_height
                    / self.__background_croped.shape[0]
                )

                rectangle_position = [int(rectangle_position[i]) for i in range(4)]

                background_to_display.astype(np.uint8)
                background_to_display = cv2.rectangle(
                    background_to_display,
                    (rectangle_position[0], rectangle_position[1]),
                    (rectangle_position[2], rectangle_position[3]),
                    (255, 0, 0),
                    3,
                )

        self.__result = background
        self.__result_display = background_to_display

    def __update_image(self, change):
        """
        Update the image displayed.
        """
        isResetButton = False
        isForwardButton = False
        isBackwardButton = False
        if type(change) == widgets.Button:
            i = change.rank
            if change.tooltip == "Reset crop":
                isResetButton = True
            elif change.description == "Up a layer":
                isForwardButton = True
            elif change.description == "Down a layer":
                isBackwardButton = True
            change = {"owner": widgets.Button(), "new": 0}
            change["owner"].description = "None"
            change["owner"].desc = None
        else:
            try:
                i = change["owner"].rank
            except AttributeError:
                i = None

        if change["owner"].description == "x:":
            self.__positions[i] = (change["new"], self.__positions[i][1])
        elif change["owner"].description == "y:":
            new_y = int(
                self.__background_croped.shape[0]
                - self.__image_heights[i]
                - change["new"]
            )
            self.__positions[i] = (self.__positions[i][0], new_y)
        elif change["owner"].description == "Opacity":
            self.__opacities[i] = change["new"]
        elif change["owner"].description == "Remove color":
            new_color = ImageColor.getcolor(
                self.__remove_widget[i].children[1].value, "RGB"
            )
            self.__remove[i][1] = list(new_color)
            if self.__remove_widget[i].children[0].value:
                self.__remove[i][0] = True
            else:
                self.__remove[i][0] = False
        elif change["owner"].description == "Color threshold":
            self.__remove[i][2] = change["new"]
        elif change["owner"].description == "Image scale":
            self.__change_image_scale(change["new"], i)
            self.__x_slider[i].min = -self.__image_widths[i]
            self.__y_slider[i].min = -self.__image_heights[i]
            self.__y_slider[i].value = (
                self.__background_croped.shape[0]
                - self.__image_heights[i]
                - self.__positions[i][1]
            )
        elif change["owner"].description == "Show image":
            self.__to_show[i] = change["new"]
        elif change["owner"].description == "Crop/expand right":
            self.__cropped[1] = -change["new"]
            self.__update_background_crop()
            self.__background_display_width = int(
                self.__background_display_height
                * (
                    self.__background_croped.shape[1]
                    / self.__background_croped.shape[0]
                )
            )
            for k in range(len(self.__images)):
                self.__x_slider[k].max = self.__background_croped.shape[1]
        elif change["owner"].description == "Crop/expand left":
            self.__cropped[3] = -change["new"]
            self.__update_background_crop()
            self.__background_display_width = int(
                self.__background_display_height
                * (
                    self.__background_croped.shape[1]
                    / self.__background_croped.shape[0]
                )
            )
            for k in range(len(self.__images)):
                self.__x_slider[k].max = self.__background_croped.shape[1]
        elif change["owner"].description == "Crop/expand top":
            self.__cropped[0] = -change["new"]
            self.__update_background_crop()
            self.__background_display_height = int(
                self.__background_display_width
                * (
                    self.__background_croped.shape[0]
                    / self.__background_croped.shape[1]
                )
            )
            for k in range(len(self.__images)):
                self.__y_slider[k].max = self.__background_croped.shape[0]
        elif change["owner"].description == "Crop/expand bottom":
            self.__cropped[2] = -change["new"]
            self.__update_background_crop()
            self.__background_display_height = int(
                self.__background_display_width
                * (
                    self.__background_croped.shape[0]
                    / self.__background_croped.shape[1]
                )
            )
            for k in range(len(self.__images)):
                self.__y_slider[k].max = self.__background_croped.shape[0]
        elif change["owner"].desc == "Crop top":
            self.__images_crop[i][0] = change["new"]
        elif change["owner"].desc == "Crop bottom":
            self.__images_crop[i][2] = change["new"]
        elif change["owner"].desc == "Crop left":
            self.__images_crop[i][3] = change["new"]
        elif change["owner"].desc == "Crop right":
            self.__images_crop[i][1] = change["new"]
        elif isResetButton:
            self.__image_crop_bottom[i].value = 0
            self.__image_crop_left[i].value = 0
            self.__image_crop_right[i].value = 0
            self.__image_crop_top[i].value = 0
        elif isBackwardButton:
            self.__backward_button[i].disabled = True
            self.__images.insert(i + 1, self.__images.pop(i))
            self.__positions.insert(i + 1, self.__positions.pop(i))
            self.__opacities.insert(i + 1, self.__opacities.pop(i))
            self.__image_scales.insert(i + 1, self.__image_scales.pop(i))
            self.__remove.insert(i + 1, self.__remove.pop(i))
            self.__to_show.insert(i + 1, self.__to_show.pop(i))
            self.__images_crop.insert(i + 1, self.__images_crop.pop(i))
            self.__image_heights.insert(i + 1, self.__image_heights.pop(i))
            self.__image_widths.insert(i + 1, self.__image_widths.pop(i))
            self.__swap_widgets(i, i + 1)
            self.__create_image()
            self.__update_code()
            self.__image_output.clear_output(wait=True)
            with self.__image_output:
                display(Image.fromarray(self.__result_display))
            self.__tab.selected_index = i + 1
            self.__backward_button[i].disabled = False
        elif isForwardButton:
            self.__forward_button[i].disabled = True
            self.__images.insert(i - 1, self.__images.pop(i))
            self.__positions.insert(i - 1, self.__positions.pop(i))
            self.__opacities.insert(i - 1, self.__opacities.pop(i))
            self.__image_scales.insert(i - 1, self.__image_scales.pop(i))
            self.__remove.insert(i - 1, self.__remove.pop(i))
            self.__to_show.insert(i - 1, self.__to_show.pop(i))
            self.__images_crop.insert(i - 1, self.__images_crop.pop(i))
            self.__image_heights.insert(i - 1, self.__image_heights.pop(i))
            self.__image_widths.insert(i - 1, self.__image_widths.pop(i))
            self.__swap_widgets(i, i - 1)
            self.__create_image()
            self.__update_code()
            self.__image_output.clear_output(wait=True)
            with self.__image_output:
                display(Image.fromarray(self.__result_display))
            self.__tab.selected_index = i - 1
            self.__forward_button[i].disabled = False

        self.__update_code()
        self.__create_image()
        self.__image_output.clear_output(wait=True)
        with self.__image_output:
            display(Image.fromarray(self.__result_display))

    def __swap_widgets(self, i, j):
        widgets_to_swap = [
            self.__x_slider,
            self.__y_slider,
            self.__remove_widget_check,
            self.__opacity_slider,
            self.__image_scale_slider,
            self.__to_show,
            self.__remove_widget_threshold,
            self.__image_crop_right,
            self.__image_crop_left,
            self.__image_crop_top,
            self.__image_crop_bottom,
            self.__reset_crop_button,
            self.__forward_button,
            self.__backward_button,
        ]
        to_change = ["value", "max", "min", "disabled"]
        for widget in widgets_to_swap:
            the_list = list(vars(widget[0])["_trait_values"]).copy()
            the_list = [
                the_list[i] for i in range(len(the_list)) if the_list[i] in to_change
            ]
            for attribute in the_list:
                save_value = getattr(widget[i], attribute)
                setattr(widget[i], attribute, getattr(widget[j], attribute))
                setattr(widget[j], attribute, save_value)
        for k in range(len(self.__forward_button)):
            self.__forward_button[k].disabled = False
            self.__backward_button[k].disabled = False
        self.__forward_button[0].disabled = True
        self.__backward_button[-1].disabled = True

    def editor(self):
        """
        Create a widget to edit the blended image.

        Returns
        -------
        ipywidgets.widgets
            Widget to edit the blended image.
        """

        tab_contents = [f"Image {i}" for i in range(len(self.__images))]
        children = [widgets.Text(description=name) for name in tab_contents]
        titles = ["Image 1 (front)"]
        titles += [f"Image {i+1}" for i in range(1, len(self.__images) - 1)]
        i = len(self.__images)
        titles += [f"Image {i} (back)", "Upload new image"]
        self.__tab = widgets.Tab(
            children=children,
            titles=titles,
        )

        def change_of_tab(b):
            self.__create_image()
            self.__image_output.clear_output(wait=True)
            with self.__image_output:
                display(Image.fromarray(self.__result_display))

        self.__tab.observe(change_of_tab)
        self.__x_slider = [None] * len(children)
        self.__y_slider = [None] * len(children)
        self.__remove_widget = [None] * len(children)
        self.__opacity_slider = [None] * len(children)
        self.__image_scale_slider = [None] * len(children)
        self.__to_show = [None] * len(children)
        self.__remove_widget_threshold = [None] * len(children)
        self.__image_crop_right = [None] * len(children)
        self.__image_crop_left = [None] * len(children)
        self.__image_crop_top = [None] * len(children)
        self.__image_crop_bottom = [None] * len(children)
        self.__reset_crop_button = [None] * len(children)
        self.__forward_button = [None] * len(children)
        self.__backward_button = [None] * len(children)
        self.__remove_widget_check = [None] * len(children)

        self.__to_display = [None] * len(children)

        self.__image_output = widgets.Output()

        def create_widgets():
            for i in range(len(self.__images)):
                self.__x_slider[i] = widgets.IntSlider(
                    value=self.__positions[i][0],
                    min=-self.__image_widths[i],
                    max=self.__background_croped.shape[1],
                    step=1,
                    description="x:",
                    disabled=False,
                    continuous_update=True,
                    orientation="horizontal",
                    readout=False,
                    readout_format="d",
                    # add margins
                    layout=widgets.Layout(
                        width=str(self.__background_display_width) + "px",
                        margin="0px 0px 0px 50px",
                    ),
                )
                self.__y_slider[i] = widgets.IntSlider(
                    value=self.__background_croped.shape[0]
                    - self.__image_heights[i]
                    - self.__positions[i][1],
                    min=-self.__image_heights[i],
                    max=self.__background_croped.shape[0],
                    step=1,
                    description="y:",
                    disabled=False,
                    continuous_update=True,
                    orientation="vertical",
                    readout=False,
                    readout_format="d",
                    layout=widgets.Layout(
                        height=str(self.__background_display_height) + "px"
                    ),
                )
                self.__to_show[i] = widgets.Checkbox(
                    value=True,
                    description="Show image",
                    disabled=False,
                    indent=True,
                )
                self.__opacity_slider[i] = widgets.FloatSlider(
                    value=self.__opacities[i],
                    min=0,
                    max=1,
                    step=0.01,
                    description="Opacity",
                    disabled=False,
                    continuous_update=True,
                    orientation="horizontal",
                    readout=True,
                    readout_format=".2f",
                )
                self.__image_scale_slider[i] = widgets.FloatSlider(
                    value=self.__image_scales[i],
                    min=0.01,
                    max=2,
                    step=0.01,
                    description="Image scale",
                    disabled=False,
                    continuous_update=True,
                    orientation="horizontal",
                    readout=True,
                    readout_format=".2f",
                )
                self.__image_crop_right[i] = widgets.BoundedIntText(
                    value=self.__images_crop[i][1],
                    min=0,
                    max=self.__images[i].shape[1] - 1,
                    step=1,
                    description="",
                    disabled=False,
                    continuous_update=True,
                    style={
                        "description_width": "initial",
                    },
                    layout=widgets.Layout(width="60px"),
                )
                self.__image_crop_right[i].desc = "Crop right"
                self.__image_crop_left[i] = widgets.BoundedIntText(
                    value=self.__images_crop[i][3],
                    min=0,
                    max=self.__images[i].shape[1] - 1,
                    step=1,
                    description="",
                    disabled=False,
                    continuous_update=True,
                    style={
                        "description_width": "initial",
                    },
                    layout=widgets.Layout(width="60px"),
                )
                self.__image_crop_left[i].desc = "Crop left"
                self.__image_crop_top[i] = widgets.BoundedIntText(
                    value=self.__images_crop[i][0],
                    min=0,
                    max=100,
                    step=1,
                    description="",
                    disabled=False,
                    continuous_update=True,
                    style={
                        "description_width": "initial",
                    },
                    layout=widgets.Layout(width="60px"),
                )
                self.__image_crop_top[i].desc = "Crop top"
                self.__image_crop_bottom[i] = widgets.BoundedIntText(
                    value=self.__images_crop[i][2],
                    min=0,
                    max=self.__images[i].shape[0] - 1,
                    step=1,
                    description="",
                    disabled=False,
                    continuous_update=True,
                    style={
                        "description_width": "initial",
                    },
                    layout=widgets.Layout(width="60px"),
                )
                self.__image_crop_bottom[i].desc = "Crop bottom"
                self.__reset_crop_button[i] = widgets.Button(
                    description="",
                    layout={"width": "60px"},
                    icon="undo",
                    tooltip="Reset crop",
                )
                # checkbox
                self.__remove_widget_check[i] = widgets.Checkbox(
                    value=deepcopy(self.__remove[i][0]),
                    description="Remove color",
                    disabled=False,
                    indent=True,
                )
                remove_widget_color = widgets.ColorPicker(
                    concise=True,
                    description="Remove color",
                    # hide description
                    style={"description_width": "0px"},
                    value="#ffffff",
                    disabled=False,
                )
                self.__remove_widget_threshold[i] = widgets.IntSlider(
                    value=deepcopy(self.__remove[i][2]),
                    min=0,
                    max=100,
                    step=1,
                    description="Color threshold",
                    disabled=False,
                    continuous_update=True,
                    orientation="horizontal",
                    readout=True,
                    readout_format="d",
                    style={
                        "description_width": "initial",
                    },
                )

                self.__remove_widget[i] = widgets.HBox(
                    [self.__remove_widget_check[i], remove_widget_color],
                )
                self.__remove_widget[i].description = "Remove color"

                self.__forward_button[i] = widgets.Button(
                    description="Up a layer",
                    disabled=False,
                    button_style="",
                    tooltip="Forward image",
                    icon="arrow-left",
                )
                self.__backward_button[i] = widgets.Button(
                    description="Down a layer",
                    disabled=False,
                    button_style="",
                    tooltip="Backward image",
                    icon="arrow-right",
                )

                self.__x_slider[i].rank = i
                self.__y_slider[i].rank = i
                self.__opacity_slider[i].rank = i
                self.__remove_widget[i].rank = i
                self.__image_scale_slider[i].rank = i
                self.__to_show[i].rank = i
                remove_widget_color.rank = i
                self.__remove_widget_threshold[i].rank = i

                self.__reset_crop_button[i].rank = i
                self.__image_crop_right[i].rank = i
                self.__image_crop_left[i].rank = i
                self.__image_crop_top[i].rank = i
                self.__image_crop_bottom[i].rank = i
                self.__forward_button[i].rank = i
                self.__backward_button[i].rank = i
                self.__remove_widget_check[i].rank = i

                # when slider changes
                self.__x_slider[i].observe(self.__update_image, names="value")
                self.__y_slider[i].observe(self.__update_image, names="value")
                self.__opacity_slider[i].observe(self.__update_image, names="value")
                self.__remove_widget[i].children[0].observe(
                    self.__update_image, names="value"
                )
                self.__remove_widget[i].children[1].observe(
                    self.__update_image, names="value"
                )
                self.__image_scale_slider[i].observe(self.__update_image, names="value")
                self.__to_show[i].observe(self.__update_image, names="value")
                self.__remove_widget_threshold[i].observe(
                    self.__update_image, names="value"
                )
                self.__image_crop_top[i].observe(self.__update_image, names="value")
                self.__image_crop_bottom[i].observe(self.__update_image, names="value")
                self.__image_crop_left[i].observe(self.__update_image, names="value")
                self.__image_crop_right[i].observe(self.__update_image, names="value")

                self.__reset_crop_button[i].on_click(self.__update_image)

                self.__forward_button[i].on_click(self.__update_image)
                self.__backward_button[i].on_click(self.__update_image)

                top = self.__x_slider[i]
                left = widgets.HBox([self.__y_slider[i], self.__image_output])
                crop_part_1 = widgets.HBox(
                    [
                        self.__image_crop_top[i],
                    ],
                    layout=widgets.Layout(justify_content="center"),
                )
                crop_part_2 = widgets.HBox(
                    [
                        self.__image_crop_left[i],
                        self.__reset_crop_button[i],
                        self.__image_crop_right[i],
                    ],
                    layout=widgets.Layout(justify_content="center"),
                )
                crop_part_3 = widgets.HBox(
                    [
                        self.__image_crop_bottom[i],
                    ],
                    layout=widgets.Layout(justify_content="center"),
                )
                crop_total = widgets.VBox(
                    [crop_part_1, crop_part_2, crop_part_3],
                    layout=widgets.Layout(justify_content="center", width="100%"),
                )
                right = widgets.VBox(
                    [
                        self.__opacity_slider[i],
                        self.__remove_widget[i],
                        self.__remove_widget_threshold[i],
                        self.__image_scale_slider[i],
                        crop_total,
                        widgets.HBox(
                            [
                                self.__forward_button[i],
                                self.__backward_button[i],
                            ],
                            layout=widgets.Layout(justify_content="center"),
                        ),
                        self.__to_show[i],
                    ],
                    layout={"justify_content": "space-around", "width": "30%"},
                )
                top_and_left = widgets.VBox([top, left])
                self.__to_display[i] = widgets.HBox(
                    [top_and_left, right],
                    layout={"width": "100%", "justify_content": "space-between"},
                )

        create_widgets()

        self.__forward_button[0].disabled = True
        self.__backward_button[-1].disabled = True

        def to_clipboard(b):
            """
            Copy code to clipboard.
            """
            to_copy = str("code = " + '"' + self.__code + '"')
            df = pd.DataFrame([to_copy])
            df.to_clipboard(index=False, header=False, excel=False, sep=None)
            # change button to green for a few seconds
            copy_button.button_style = "success"
            copy_button.description = "Copied!"
            copy_button.disabled = True
            time.sleep(2)
            copy_button.button_style = ""
            copy_button.description = "Copy code to clipboard"
            copy_button.disabled = False

        # button to copy code to clipboard
        copy_button = widgets.Button(
            description="Copy code to clipboard",
            icon="clipboard",
            layout={"width": "180px"},
        )
        copy_button.on_click(to_clipboard)

        upload_new_image = FileChooser()
        upload_new_image.filter_pattern = ["*.jpg", "*.png", "*.jpeg"]

        background_crop_right = widgets.BoundedIntText(
            value=-self.__cropped[1],
            min=-self.__background_croped.shape[1] + 10,
            max=self.__background_croped.shape[1],
            step=1,
            description="Crop/expand right",
            disabled=False,
            continuous_update=True,
            style={
                "description_width": "initial",
            },
            layout=widgets.Layout(width="18%"),
        )
        background_crop_left = widgets.BoundedIntText(
            value=-self.__cropped[3],
            min=-self.__background_croped.shape[1] + 10,
            max=self.__background_croped.shape[1],
            step=1,
            description="Crop/expand left",
            disabled=False,
            continuous_update=True,
            style={
                "description_width": "initial",
            },
            layout=widgets.Layout(width="18%"),
        )
        background_crop_top = widgets.BoundedIntText(
            value=-self.__cropped[0],
            min=-self.__background_croped.shape[0] + 10,
            max=self.__background_croped.shape[0],
            step=1,
            description="Crop/expand top",
            disabled=False,
            continuous_update=True,
            style={
                "description_width": "initial",
            },
            layout=widgets.Layout(width="18%"),
        )

        background_crop_bottom = widgets.BoundedIntText(
            value=-self.__cropped[2],
            min=-self.__background_croped.shape[0] + 10,
            max=self.__background_croped.shape[0],
            step=1,
            description="Crop/expand bottom",
            disabled=False,
            continuous_update=True,
            style={
                "description_width": "initial",
            },
            layout=widgets.Layout(width="18%"),
        )

        def reinit_crop(b):
            """
            Reinit crop.
            """
            background_crop_right.value = 0
            background_crop_left.value = 0
            background_crop_top.value = 0
            background_crop_bottom.value = 0

        reinit_button = widgets.Button(description="Reset crop", icon="undo")
        reinit_button.on_click(reinit_crop)

        background_crop_right.observe(self.__update_image, names="value")
        background_crop_left.observe(self.__update_image, names="value")
        background_crop_top.observe(self.__update_image, names="value")
        background_crop_bottom.observe(self.__update_image, names="value")

        with self.__image_output:
            display(Image.fromarray(self.__result_display))

        #    | x  x  x
        # y  |  image  | opacity
        # y  |  image  | remove
        # y  |  image  | image scale
        # code | copy button

        button_validate_upload = widgets.Button(description="Validate", disabled=True)

        part_upload_new_image = widgets.VBox(
            [
                upload_new_image,
                button_validate_upload,
            ],
        )

        def upload_image_ftc(change):
            button_validate_upload.disabled = False

        # Register callback function
        upload_new_image.register_callback(upload_image_ftc)

        def fct_upload_image(b):
            new_image = Image.open(upload_new_image.selected)
            new_image = new_image.convert("RGB")
            new_image = np.array(new_image)

            self.__images.append(new_image)
            self.__positions.append((0, 0))
            self.__opacities.append(1)
            self.__image_scales.append(0.5)
            self.__remove.append([False, [255, 255, 255], 0])
            self.__to_show.append(True)
            self.__images_crop.append([0, 0, 0, 0])
            self.__image_heights.append(
                self.__image_scales[-1] * self.__background_croped.shape[0]
            )
            self.__image_widths.append(
                self.__images[-1].shape[1]
                * (self.__image_heights[-1] / new_image.shape[0])
            )

            self.__x_slider.append(None)
            self.__y_slider.append(None)
            self.__remove_widget.append(None)
            self.__opacity_slider.append(None)
            self.__image_scale_slider.append(None)
            self.__to_show.append(None)
            self.__remove_widget_threshold.append(None)
            self.__image_crop_right.append(None)
            self.__image_crop_left.append(None)
            self.__image_crop_top.append(None)
            self.__image_crop_bottom.append(None)
            self.__reset_crop_button.append(None)
            self.__to_display.append(None)
            self.__remove_widget_check.append(None)
            self.__forward_button.append(None)
            self.__backward_button.append(None)

            create_widgets()
            self.__update_code()
            self.__create_image()
            b = widgets.Button()
            b.rank = len(self.__images) - 1
            self.__update_image(b)

            tab_contents = [f"Image {i}" for i in range(len(self.__images))]
            children = [widgets.Text(description=name) for name in tab_contents]
            titles = ["Image 1 (front)"]
            titles += [f"Image {i+1}" for i in range(1, len(self.__images) - 1)]
            titles += [f"Image {len(self.__images)} (back)", "Upload new image"]
            self.__tab = widgets.Tab(
                children=children,
                titles=titles,
            )
            self.__tab.children = self.__to_display
            self.__tab.children = list(self.__tab.children) + [part_upload_new_image]
            self.__tab.set_title(len(self.__tab.children) - 1, "Upload new image")
            self.__final.children = [self.__tab] + list(self.__final.children)[1:]

            for k in range(len(self.__backward_button)):
                self.__backward_button[k].disabled = False
                self.__forward_button[k].disabled = False
            self.__backward_button[-1].disabled = True
            self.__forward_button[0].disabled = True

        button_validate_upload.on_click(fct_upload_image)

        self.__tab.children = self.__to_display
        self.__tab.children = list(self.__tab.children) + [part_upload_new_image]
        self.__tab.set_title(len(self.__tab.children) - 1, "Upload new image")

        image_display_size = widgets.IntSlider(
            value=self.__background_display_height,
            min=100,
            max=600,
            step=1,
            description="Image display height (px):",
            disabled=False,
            continuous_update=True,
            orientation="horizontal",
            readout=True,
            readout_format="d",
            style={
                "description_width": "initial",
            },
            layout=widgets.Layout(width="40%"),
        )

        def update_image_display_size(change):
            """
            Update the image display size.
            """
            self.__background_display_height = change["new"]
            self.__background_display_width = int(
                self.__background_display_height
                * (
                    self.__background_croped.shape[1]
                    / self.__background_croped.shape[0]
                )
            )
            for k in range(len(self.__images)):
                self.__x_slider[k].layout.width = (
                    str(self.__background_display_width) + "px"
                )
                self.__y_slider[k].layout.height = (
                    str(self.__background_display_height) + "px"
                )
            self.__create_image()
            self.__image_output.clear_output(wait=True)
            with self.__image_output:
                display(Image.fromarray(self.__result_display))

        image_display_size.observe(update_image_display_size, names="value")

        visualize_layer_check = widgets.Checkbox(
            value=False, description="Visualize the current layer"
        )

        def change_vis_value(change):
            """
            Change the value of __visualize_layer.
            """
            if type(change["new"]) != dict:
                return
            if len(change["new"]) == 0:
                return
            if change["new"]["value"]:
                self.__visualize_layer = True
            else:
                self.__visualize_layer = False
            self.__create_image()
            self.__image_output.clear_output(wait=True)
            with self.__image_output:
                display(Image.fromarray(self.__result_display))

        visualize_layer_check.observe(change_vis_value)

        code_part = widgets.HBox(
            [
                copy_button,
                visualize_layer_check,
                image_display_size,
            ],
            layout=widgets.Layout(width="100%", justify_content="space-between"),
        )
        background_part = widgets.HBox(
            [
                reinit_button,
                background_crop_left,
                background_crop_right,
                background_crop_top,
                background_crop_bottom,
            ],
            layout=widgets.Layout(
                width="100%", justify_content="space-around", margin="10px 0px 10px 0px"
            ),
        )
        bottom = widgets.VBox([background_part, code_part])
        self.__final = widgets.VBox([self.__tab, bottom])

        return self.__final
