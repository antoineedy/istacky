from PIL import Image, ImageColor
import numpy as np
import ipywidgets as widgets
import cv2
import pandas as pd
import time
from copy import deepcopy
from ipyfilechooser import FileChooser
import os

from IPython.display import display


class BlendedImage:
    def __init__(
        self,
        background,
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

        if code is not None:
            if not isinstance(code, str):
                raise TypeError("code must be str")
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

        self.background = background
        self.images = images

        if isinstance(background, Image.Image):
            background = background.convert("RGB")
            self.background = np.array(background)
        elif not isinstance(background, np.array):
            raise TypeError("self.background must be PIL.Image.Image or numpy.ndarray")

        stored_images = []

        for image in images:
            if isinstance(image, Image.Image):
                image = image.convert("RGB")
                stored_images.append(np.array(image))
            elif not isinstance(image, np.array):
                raise TypeError("image must be PIL.Image.Image or numpy.ndarray")

        self.images = stored_images

        self.positions = positions
        self.opacities = opacities
        self.background_resize = background_resize
        self.image_scales = image_scales
        # remove = [True or False, Color, Threshold]
        self.remove = deepcopy(remove)
        self.__to_show = to_show
        self.background_display_height = 350
        self.background_display_width = int(
            self.background_display_height
            * (self.background.shape[1] / self.background.shape[0])
        )

        self.__image_heights = list(
            np.array(self.image_scales) * self.background.shape[0]
        )
        self.__image_widths = []
        k = 0
        for image in self.images:
            height = image.shape[1] * (self.__image_heights[k] / image.shape[0])
            self.__image_widths.append(height)
            k += 1

        self.__visualize_layer = False

        self.cropped = cropped
        self.background_croped = None
        self.images_crop = images_crop
        self.__update_background_crop()

        self.create_image()
        self.__update_code()

    def show(self):
        """
        Show the blended image.
        """
        display(Image.fromarray(self.result))

    def get_code(self):
        """
        Get the code to reproduce the blended image.
        """
        return self.code

    def __update_code(self):
        """
        Update the code.
        """
        self.code = ""
        for k in range(len(self.images)):
            self.code += (
                "#"
                + str(round(self.image_scales[k], 4))
                + "-"
                + str(int(self.positions[k][0]))
                + "-"
                + str(int(self.positions[k][1]))
                + "-"
                + str(round(self.opacities[k], 4))
                + "-"
                + str(1 if self.remove[k][0] else 0)
                + "-"
                + str(self.remove[k][1])[1:-1].replace(" ", "")
                + "-"
                + str(self.remove[k][2])
                + "-"
                + str(1 if self.__to_show[k] else 0)
                + "-"
                + str(self.images_crop[k])[1:-1].replace(" ", "")
            )
        self.code += "c" + str(self.cropped)[1:-1].replace(" ", "")

    def __change_image_scale(self, change, k):
        """
        Change the image scale.
        """
        self.image_scales[k] = change
        self.__image_heights[k] = self.image_scales[k] * self.background_croped.shape[0]
        self.__image_widths[k] = self.images[k].shape[1] * (
            self.__image_heights[k] / self.images[k].shape[0]
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

        if remove[0]:
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

        if remove[0]:
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
        the_back = self.background.copy()
        the_back = Image.fromarray(the_back)
        the_back = the_back.crop(
            (
                self.cropped[3],
                self.cropped[0],
                the_back.width - self.cropped[1],
                the_back.height - self.cropped[2],
            )
        )
        self.background_croped = np.array(the_back)

    def create_image(self):
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

        background = self.background_croped.copy()
        images = self.images.copy()

        # resize self.background_croped
        if self.background_resize is not None:
            background = Image.fromarray(background)
            background = background.resize(
                (
                    int(background.width * self.background_resize),
                    int(background.height * self.background_resize),
                )
            )
            background = np.array(self.background_croped)

        for k in range(len(images)):
            image = images[k]
            image = Image.fromarray(image)
            new_height = background.shape[0] * self.image_scales[k]
            new_width = image.width * (new_height / image.height)
            image = image.resize((int(new_width), int(new_height)))
            image = np.array(image)
            images[k] = image

        # blend the background part and the image
        for k in range(len(self.images))[::-1]:
            if not self.__to_show[k]:
                continue
            background = self.__blend_arrays(
                background,
                images[k],
                self.opacities[k],
                self.remove[k],
                self.positions[k],
                self.images_crop[k],
            )

        background_to_display = background.copy()
        background_to_display = Image.fromarray(background_to_display)
        background_to_display = background_to_display.convert("RGBA")
        background_to_display = background_to_display.resize(
            (
                self.background_display_width,
                self.background_display_height,
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
            # put red rectangle on selected image
            image_crop = [int(self.images_crop[k][i]) for i in range(4)]
            # now in pixel (it was in percent):
            image_crop[0] = image_crop[0] * self.__image_heights[k] / 100
            image_crop[2] = image_crop[2] * self.__image_heights[k] / 100
            image_crop[1] = image_crop[1] * self.__image_widths[k] / 100
            image_crop[3] = image_crop[3] * self.__image_widths[k] / 100
            rectangle_position = [
                self.positions[k][0],
                self.positions[k][1],
                self.positions[k][0]
                + self.__image_widths[k]
                - image_crop[1]
                - image_crop[3],
                self.positions[k][1]
                + self.__image_heights[k]
                - image_crop[0]
                - image_crop[2],
            ]
            rectangle_position = [
                int(i * self.background_display_width / self.background.shape[1])
                for i in rectangle_position
            ]
            background_to_display.astype(np.uint8)
            background_to_display = cv2.rectangle(
                background_to_display,
                (rectangle_position[0], rectangle_position[1]),
                (rectangle_position[2], rectangle_position[3]),
                (255, 0, 0),
                3,
            )

        self.result = background
        self.result_display = background_to_display

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
            self.positions[i] = (change["new"], self.positions[i][1])
        elif change["owner"].description == "y:":
            new_y = int(
                self.background_croped.shape[0]
                - self.__image_heights[i]
                - change["new"]
            )
            self.positions[i] = (self.positions[i][0], new_y)
        elif change["owner"].description == "Opacity":
            self.opacities[i] = change["new"]
        elif change["owner"].description == "Remove color":
            new_color = ImageColor.getcolor(
                self.__remove_widget[i].children[1].value, "RGB"
            )
            self.remove[i][1] = list(new_color)
            if self.__remove_widget[i].children[0].value:
                self.remove[i][0] = True
            else:
                self.remove[i][0] = False
        elif change["owner"].description == "Color threshold":
            self.remove[i][2] = change["new"]
        elif change["owner"].description == "Image scale":
            self.__change_image_scale(change["new"], i)
            self.__x_slider[i].min = -self.__image_widths[i]
            self.__y_slider[i].min = -self.__image_heights[i]
            self.__y_slider[i].value = (
                self.background_croped.shape[0]
                - self.__image_heights[i]
                - self.positions[i][1]
            )
        elif change["owner"].description == "Show image":
            self.__to_show[i] = change["new"]
        elif change["owner"].description == "Crop/expand right":
            self.cropped[1] = -change["new"]
            self.__update_background_crop()
            self.background_display_width = int(
                self.background_display_height
                * (self.background_croped.shape[1] / self.background_croped.shape[0])
            )
            for k in range(len(self.images)):
                self.__x_slider[k].max = self.background_croped.shape[1]
        elif change["owner"].description == "Crop/expand left":
            self.cropped[3] = -change["new"]
            self.__update_background_crop()
            self.background_display_width = int(
                self.background_display_height
                * (self.background_croped.shape[1] / self.background_croped.shape[0])
            )
            for k in range(len(self.images)):
                self.__x_slider[k].max = self.background_croped.shape[1]
        elif change["owner"].description == "Crop/expand top":
            self.cropped[0] = -change["new"]
            self.__update_background_crop()
            self.background_display_height = int(
                self.background_display_width
                * (self.background_croped.shape[0] / self.background_croped.shape[1])
            )
            for k in range(len(self.images)):
                self.__y_slider[k].max = self.background_croped.shape[0]
        elif change["owner"].description == "Crop/expand bottom":
            self.cropped[2] = -change["new"]
            self.__update_background_crop()
            self.background_display_height = int(
                self.background_display_width
                * (self.background_croped.shape[0] / self.background_croped.shape[1])
            )
            for k in range(len(self.images)):
                self.__y_slider[k].max = self.background_croped.shape[0]
        elif change["owner"].desc == "Crop top":
            self.images_crop[i][0] = change["new"]
        elif change["owner"].desc == "Crop bottom":
            self.images_crop[i][2] = change["new"]
        elif change["owner"].desc == "Crop left":
            self.images_crop[i][3] = change["new"]
        elif change["owner"].desc == "Crop right":
            self.images_crop[i][1] = change["new"]
        elif isResetButton:
            self.__image_crop_bottom[i].value = 0
            self.__image_crop_left[i].value = 0
            self.__image_crop_right[i].value = 0
            self.__image_crop_top[i].value = 0
        elif isBackwardButton:
            self.__backward_button[i].disabled = True
            self.images.insert(i + 1, self.images.pop(i))
            self.positions.insert(i + 1, self.positions.pop(i))
            self.opacities.insert(i + 1, self.opacities.pop(i))
            self.image_scales.insert(i + 1, self.image_scales.pop(i))
            self.remove.insert(i + 1, self.remove.pop(i))
            self.__to_show.insert(i + 1, self.__to_show.pop(i))
            self.images_crop.insert(i + 1, self.images_crop.pop(i))
            self.__image_heights.insert(i + 1, self.__image_heights.pop(i))
            self.__image_widths.insert(i + 1, self.__image_widths.pop(i))
            self.__swap_widgets(i, i + 1)
            self.create_image()
            self.__update_code()
            self.__image_output.clear_output(wait=True)
            with self.__image_output:
                display(Image.fromarray(self.result_display))
            self.__tab.selected_index = i + 1
            self.__backward_button[i].disabled = False
        elif isForwardButton:
            self.__forward_button[i].disabled = True
            self.images.insert(i - 1, self.images.pop(i))
            self.positions.insert(i - 1, self.positions.pop(i))
            self.opacities.insert(i - 1, self.opacities.pop(i))
            self.image_scales.insert(i - 1, self.image_scales.pop(i))
            self.remove.insert(i - 1, self.remove.pop(i))
            self.__to_show.insert(i - 1, self.__to_show.pop(i))
            self.images_crop.insert(i - 1, self.images_crop.pop(i))
            self.__image_heights.insert(i - 1, self.__image_heights.pop(i))
            self.__image_widths.insert(i - 1, self.__image_widths.pop(i))
            self.__swap_widgets(i, i - 1)
            self.create_image()
            self.__update_code()
            self.__image_output.clear_output(wait=True)
            with self.__image_output:
                display(Image.fromarray(self.result_display))
            self.__tab.selected_index = i - 1
            self.__forward_button[i].disabled = False

        self.__update_code()
        self.create_image()
        self.__image_output.clear_output(wait=True)
        with self.__image_output:
            display(Image.fromarray(self.result_display))

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
        """

        tab_contents = [f"Image {i}" for i in range(len(self.images))]
        children = [widgets.Text(description=name) for name in tab_contents]
        titles = ["Image 1 (front)"]
        titles += [f"Image {i+1}" for i in range(1, len(self.images) - 1)]
        i = len(self.images)
        titles += [f"Image {i} (back)", "Upload new image"]
        self.__tab = widgets.Tab(
            children=children,
            titles=titles,
        )

        def change_of_tab(b):
            self.create_image()
            self.__image_output.clear_output(wait=True)
            with self.__image_output:
                display(Image.fromarray(self.result_display))

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
            for i in range(len(self.images)):
                self.__x_slider[i] = widgets.IntSlider(
                    value=self.positions[i][0],
                    min=-self.__image_widths[i],
                    max=self.background_croped.shape[1],
                    step=1,
                    description="x:",
                    disabled=False,
                    continuous_update=True,
                    orientation="horizontal",
                    readout=False,
                    readout_format="d",
                    # add margins
                    layout=widgets.Layout(
                        width=str(self.background_display_width) + "px",
                        margin="0px 0px 0px 50px",
                    ),
                )
                self.__y_slider[i] = widgets.IntSlider(
                    value=self.background_croped.shape[0]
                    - self.__image_heights[i]
                    - self.positions[i][1],
                    min=-self.__image_heights[i],
                    max=self.background_croped.shape[0],
                    step=1,
                    description="y:",
                    disabled=False,
                    continuous_update=True,
                    orientation="vertical",
                    readout=False,
                    readout_format="d",
                    layout=widgets.Layout(
                        height=str(self.background_display_height) + "px"
                    ),
                )
                self.__to_show[i] = widgets.Checkbox(
                    value=True,
                    description="Show image",
                    disabled=False,
                    indent=True,
                )
                self.__opacity_slider[i] = widgets.FloatSlider(
                    value=self.opacities[i],
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
                    value=self.image_scales[i],
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
                    value=self.images_crop[i][1],
                    min=0,
                    max=self.images[i].shape[1] - 1,
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
                    value=self.images_crop[i][3],
                    min=0,
                    max=self.images[i].shape[1] - 1,
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
                    value=self.images_crop[i][0],
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
                    value=self.images_crop[i][2],
                    min=0,
                    max=self.images[i].shape[0] - 1,
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
                    value=deepcopy(self.remove[i][0]),
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
                    value=deepcopy(self.remove[i][2]),
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
            to_copy = str("code = " + '"' + self.code + '"')
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
            value=0,
            min=-self.background_croped.shape[1] + 10,
            max=self.background_croped.shape[1],
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
            value=0,
            min=-self.background_croped.shape[1] + 10,
            max=self.background_croped.shape[1],
            step=5,
            description="Crop/expand left",
            disabled=False,
            continuous_update=True,
            style={
                "description_width": "initial",
            },
            layout=widgets.Layout(width="18%"),
        )
        background_crop_top = widgets.BoundedIntText(
            value=0,
            min=-self.background_croped.shape[0] + 10,
            max=self.background_croped.shape[0],
            step=5,
            description="Crop/expand top",
            disabled=False,
            continuous_update=True,
            style={
                "description_width": "initial",
            },
            layout=widgets.Layout(width="18%"),
        )

        background_crop_bottom = widgets.BoundedIntText(
            value=0,
            min=-self.background_croped.shape[0] + 10,
            max=self.background_croped.shape[0],
            step=5,
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
            display(Image.fromarray(self.result_display))

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

            self.images.append(new_image)
            self.positions.append((0, 0))
            self.opacities.append(1)
            self.image_scales.append(0.5)
            self.remove.append([False, [255, 255, 255], 0])
            self.__to_show.append(True)
            self.images_crop.append([0, 0, 0, 0])
            self.__image_heights.append(
                self.image_scales[-1] * self.background_croped.shape[0]
            )
            self.__image_widths.append(
                self.images[-1].shape[1]
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
            self.create_image()
            b = widgets.Button()
            b.rank = len(self.images) - 1
            self.__update_image(b)

            tab_contents = [f"Image {i}" for i in range(len(self.images))]
            children = [widgets.Text(description=name) for name in tab_contents]
            titles = ["Image 1 (front)"]
            titles += [f"Image {i+1}" for i in range(1, len(self.images) - 1)]
            titles += [f"Image {len(self.images)} (back)", "Upload new image"]
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
            value=self.background_display_height,
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
            self.background_display_height = change["new"]
            self.background_display_width = int(
                self.background_display_height
                * (self.background_croped.shape[1] / self.background_croped.shape[0])
            )
            for k in range(len(self.images)):
                self.__x_slider[k].layout.width = (
                    str(self.background_display_width) + "px"
                )
                self.__y_slider[k].layout.height = (
                    str(self.background_display_height) + "px"
                )
            self.create_image()
            self.__image_output.clear_output(wait=True)
            with self.__image_output:
                display(Image.fromarray(self.result_display))

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
            self.create_image()
            self.__image_output.clear_output(wait=True)
            with self.__image_output:
                display(Image.fromarray(self.result_display))

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

        display(self.__final)
