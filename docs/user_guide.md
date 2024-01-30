<a name="top-of-the-page"></a>

## Installation

#### Using pip: _(recommended)_
```sh
pip install istacky
```

#### Install and run from source code:

Clone the repo, create a virtual environment and then install using pip:
```sh
git clone https://github.com/antoineedy/istacky.git
cd istacky
python3 -m venv .
source bin/activate
pip install -e .
```

!!! warning
    The [Ipywidgets library](https://github.com/jupyter-widgets/ipywidgets) is not very stable when used in VSCode. `nbclient` and `nbconvert` are two requirements that will be automatically downloaded when installing IStacky, and that should make the library work in VSCode. However, if you encounter any problem, please use [Jupyter Lab](https://jupyter.org/) instead

<!-- USAGE EXAMPLES -->
## Usage

!!! example
    Have a look at [this notebook](https://github.com/antoineedy/istacky/blob/main/example.ipynb) for an example you can run at home!

#### :video_camera: Video tutorial

Access the French version [here](https://www.youtube.com/watch?v=z5O9oRozJD0).

!!! quote ""
    === "English version"
        <iframe width="560" height="315" src="https://www.youtube.com/embed/see3Uufp0Q4?si=o9d2GthbzOZ6X5Fo" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" allowfullscreen></iframe>

    === "French version"
        <iframe width="560" height="315" src="https://www.youtube.com/embed/z5O9oRozJD0?si=9akS2JO6L-s21cKE" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" allowfullscreen></iframe>

#### :notebook: Example

In our example, we want to create an output image, with a tennis point in background, and some plots, a circle and a logo on top of it. We will first import the libraries needed:
```python
from PIL import Image
import istacky
```

Then load the images we want to stack:
```python
background = Image.open("image/background.png")
plot = Image.open("image/plot.png")
circle = Image.open("image/circle.png")
logo = Image.open("image/logo.png")
```

Create a `BlendedImage` object and display it:
```python
blended = istacky.BlendedImage(background, [plot, circle, logo])
blended.show()
```
![First output](https://raw.githubusercontent.com/antoineedy/istacky/main/docs/img/output_bad.png "Title")

The images are just stacked on top of each other! Let's apply some modifications to them:
```python
blended.editor()
```
![Editor](https://raw.githubusercontent.com/antoineedy/istacky/main/docs/img/editor.png "Title")

Calling editor displays a widget that allows you to apply modifications to the images. You can crop, resize, change the opacity, remove the background, add images, change the orders of the layers etc. In our case, we want to put the logo in one corner, circle the position of the ball and add a plot of the trajectory of the ball. After the changes, here is the final result:

```python
blended.show()
```
![Final output](https://raw.githubusercontent.com/antoineedy/istacky/main/docs/img/output_good.png "Title")

Now, if we want to apply the same modifications to another image, we can have access to the code that was used to create the final image, and apply it to another one:
```python
my_code = blended.get_code()
```
Let's import the new images.
```python
background2 = Image.open("image/background2.png")
plot2 = Image.open("image/plot2.png")
circle2 = Image.open("image/circle2.png")
``` 
We specify the code that was used to create the first image, and apply it to the new images:
```python
new_blended = istacky.BlendedImage(
    background=plot2,
    images = [plot2, circle2, logo],
    code=my_code
    )
    
new_blended.show()
```
![Final output](https://raw.githubusercontent.com/antoineedy/istacky/main/docs/img/output_good2.png "Title")

We can see that the modifications have been applied to the new images!

## :gear: GUI options

| Widget  | Function  | Values  |
|:---:|---|---|
| <img src=https://raw.githubusercontent.com/antoineedy/istacky/main/docs/img/widgets/layers.png  alt="Logo" width="300"> | Switch between layers  | $l \in ⟦1, N_{images}⟧$  <tr></tr>|
|<img src=https://raw.githubusercontent.com/antoineedy/istacky/main/docs/img/widgets/x.png  alt="Logo" width="150"> | Reposition the image ($x$ and $y$ coordinates)  | $x \in [-I_{w}, Bg_{w} + I{w}]$  <br/>$y \in [-Y_{h}, Bg_{h} + I_{h}]$  <tr></tr>|
|<img src=https://raw.githubusercontent.com/antoineedy/istacky/main/docs/img/widgets/opacity.png  alt="Logo" width="250"> | Change the opacity of the selected layer  | $o\in[0, 1]$  <tr></tr>|
| <img src=https://raw.githubusercontent.com/antoineedy/istacky/main/docs/img/widgets/remove.png  alt="Logo" width="150">  | Remove one color of the selected layer | $[r, g, b] \in ⟦0, 255⟧^3$  <tr></tr>|
| <img src=https://raw.githubusercontent.com/antoineedy/istacky/main/docs/img/widgets/threshold.png  alt="Logo" width="200">   | How close the removed colors must be from the selected color | $t\in[0, 100]$  <tr></tr>|
| <img src=https://raw.githubusercontent.com/antoineedy/istacky/main/docs/img/widgets/scale.png  alt="Logo" width="200">  | The height of the selected image in % of the background height  | $s\in]0, 2]$  <tr></tr>|
| <img src=https://raw.githubusercontent.com/antoineedy/istacky/main/docs/img/widgets/crop_im.png  alt="Logo" width="150">  | Percentage of the selected image cropped in all 4 directions, and reseting the crop  |$c\in[0, 100]$  <tr></tr>|
| <img src=https://raw.githubusercontent.com/antoineedy/istacky/main/docs/img/widgets/show.png  alt="Logo" width="120">  | Show the selected layer in the final image  | $s\in\{True, False\}$  <tr></tr>|
| <img src=https://raw.githubusercontent.com/antoineedy/istacky/main/docs/img/widgets/crop_expand.png  alt="Logo" width="200">  | Crop or expand the background image (in pixels) in all 4 directions | $c\in \mathbb{Z}$  <tr></tr>|
| <img src=https://raw.githubusercontent.com/antoineedy/istacky/main/docs/img/widgets/reset.png  alt="Logo" width="150">  | Reset the cropping of the background  |   <tr></tr>|
| <img src=https://raw.githubusercontent.com/antoineedy/istacky/main/docs/img/widgets/copy.png  alt="Logo" width="200">  | Copy the code of the current output to the clipboard  |   <tr></tr>|
| <img src=https://raw.githubusercontent.com/antoineedy/istacky/main/docs/img/widgets/visualize.png  alt="Logo" width="200">  | Make a red border appear on the selected layer for editing purposes (does not appear on the final output)  | $v\in\{True, False\}$ <tr></tr> |
| <img src=https://raw.githubusercontent.com/antoineedy/istacky/main/docs/img/widgets/display.png  alt="Logo" width="220">  | Set the size of the image displayed in pixels to fit all screen sizes (does not change the output size) | $d\in]0, 1000]$  <tr></tr>|
| <img src=https://raw.githubusercontent.com/antoineedy/istacky/main/docs/img/widgets/add_image.png  alt="Logo" width="150">  | Upload a new image to stack. Creates a new layer.  |   <tr></tr>|
| <img src=https://raw.githubusercontent.com/antoineedy/istacky/main/docs/img/widgets/add.png  alt="Logo" width="400">  | To choose the new image to add from the user's computer. Made with [ipyfilechooser](https://github.com/crahan/ipyfilechooser)  |   <tr></tr>|
