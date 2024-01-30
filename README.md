<a name="readme-top"></a>

<div align="center">

[![Contributors][contributors-shield]][contributors-url] [![Forks][forks-shield]][forks-url] [![Stargazers][stars-shield]][stars-url] [![Issues][issues-shield]][issues-url] [![MIT License][license-shield]][license-url] [![LinkedIn][linkedin-shield]][linkedin-url]

</div>

<!-- PROJECT LOGO -->
<br />
<div align="center">
  <a href="https://github.com/antoineedy/istacky">
    <img src="https://raw.githubusercontent.com/antoineedy/istacky/main/docs/img/logo.png" alt="Logo" height="120">
  </a>

<h3 align="center">IStacky</h3>

  <p align="center">
    A Python lightweight image processing library
    <br />
    <a href="https://antoineedy.github.io/istacky"><strong>Explore the docs »</strong></a>
    <br />
    <br />
    <a href="https://github.com/antoineedy/istacky/blob/main/example.ipynb">Example</a>
    ·
    <a href="https://github.com/antoineedy/istacky/blob/main/CHANGELOG.md">Changelog</a>
    ·
    <a href="https://github.com/antoineedy/istacky/blob/main/TODO.md">Todo List</a>
    .
    <a href="https://pypi.org/project/istacky/">PyPi</a>
  </p>
</div>

---

## :books: About The Project

<div align="center">

[![Usage of istacky][product-screenshot]](https://github.com/antoineedy/istacky/blob/main/docs/img/gif1.gif)

</div>

__IStacky__ is a __Python lightweight image processing library__ based on the [ipywidgets](https://github.com/jupyter-widgets/ipywidgets) library and designed to be used in [Jupyter Notebooks](https://jupyter.org/). The main idea is to provide a __simple__ and __intuitive interface__ to __stack images__ and apply number of modifications to them, such as __cropping__, __resizing__ or __background removal__.

This project has been made to be used in the context of __machine learning__ and __computer vision projects__, where the user needs to __quickly__ and __easily__ create output images that combines several images: plots, photos, logos etc.

<p align="right">(<a href="#readme-top">back to top</a>)</p>


## :technologist: Installation

__using pip:__ _(recommended)_
```sh
pip install istacky
```

__from source code:__

Clone the repo, create a virtual environment and install using pip:
```sh
git clone https://github.com/antoineedy/istacky.git
cd istacky
python3 -m venv .
source bin/activate
pip install -e .
```

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- USAGE EXAMPLES -->
## :mag_right: Usage

IStacky is meant to be used in Jupyter Notebooks. Do not forget to have a look at the [documentation](https://antoineedy.github.io/istacky) for more details! You can also access the a look at the [example notebook](https://github.com/antoineedy/istacky/blob/main/example.ipynb) for an example you can run at home.

#### :video_camera: Video tutorial

<div align="center">
  <a href="https://www.youtube.com/watch?v=see3Uufp0Q4&t=3s"><img src="https://raw.githubusercontent.com/antoineedy/istacky/main/docs/img/yt_video.png" alt="IMAGE ALT TEXT" height="220"></a>
</div>
<div align="center">
  <br>
Access the French version <a href="https://www.youtube.com/watch?v=z5O9oRozJD0">here</a>.
</div>

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


<p align="right">(<a href="#readme-top">back to top</a>)</p>

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


<!-- ROADMAP -->
## :world_map: Future of the project

I wonder if I (we?) should extend this project to create a Photoshop-like interface using the ipywidgets library. I really don't know any use to this project. Either way, __[click here to access the todo list](https://github.com/antoineedy/istacky/blob/main/TODO.md")__ which contains the list of things to do for the project, and let me know if you have any ideas!

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- CONTRIBUTING -->
## :family_man_woman_girl_boy: Contributing

If you have a suggestion that would make this better, please fork the repo and create a pull request. You can also simply open an issue with the tag "enhancement".

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/MyFeature`)
3. Commit your Changes (`git commit -m 'Would be great!'`)
4. Push to the Branch (`git push origin feature/MyFeature`)
5. Open a Pull Request

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- LICENSE -->
## :scroll: License

Distributed under the MIT License. See [`LICENSE`](LICENSE) for more information.

<p align="right">(<a href="#readme-top">back to top</a>)</p>



<!-- CONTACT -->
## :dart: Contact

My name is Antoine EDY. Here are my [LinkedIn](https://www.linkedin.com/in/antoineedy/) and my [Github](https://github.com/antoineedy) profiles, and you can send me an email to [antoineedy@outlook.fr](mailto:antoineedy@outlook.fr).

<p align="right">(<a href="#readme-top">back to top</a>)</p>


<!-- MARKDOWN LINKS & IMAGES -->
<!-- https://www.markdownguide.org/basic-syntax/#reference-style-links -->
[contributors-shield]: https://img.shields.io/github/contributors/antoineedy/istacky?style=for-the-badge
[contributors-url]: https://github.com/antoineedy/istacky/graphs/contributors
[forks-shield]: https://img.shields.io/github/forks/antoineedy/istacky?style=for-the-badge
[forks-url]: https://github.com/antoineedy/istacky/network/members
[stars-shield]: https://img.shields.io/github/stars/antoineedy/istacky?style=for-the-badge
[stars-url]: https://github.com/antoineedy/istacky/stargazers
[issues-shield]: https://img.shields.io/github/issues/antoineedy/istacky?style=for-the-badge
[issues-url]: https://github.com/antoineedy/istacky/issues
[license-shield]: https://img.shields.io/github/license/antoineedy/istacky?style=for-the-badge
[license-url]: https://github.com/antoineedy/istacky/blob/master/LICENSE.txt
[linkedin-shield]: https://img.shields.io/badge/-LinkedIn-black.svg?style=for-the-badge&logo=linkedin&colorB=555
[linkedin-url]: https://linkedin.com/in/antoineedy
[product-screenshot]: https://raw.githubusercontent.com/antoineedy/istacky/main/docs/img/gif1.gif

[widget-layers]: https://raw.githubusercontent.com/antoineedy/istacky/main/docs/img/widgets/layers.png 
[widget-add]: https://raw.githubusercontent.com/antoineedy/istacky/main/docs/img/widgets/add.png
[widget-remove]: https://raw.githubusercontent.com/antoineedy/istacky/main/docs/img/widgets/remove.png
[widget-crop-im]: https://raw.githubusercontent.com/antoineedy/istacky/main/docs/img/widgets/crop_im.png
[widget-crop-expand]: https://raw.githubusercontent.com/antoineedy/istacky/main/docs/img/widgets/crop_expand.png
[widget-display]: https://raw.githubusercontent.com/antoineedy/istacky/main/docs/img/widgets/display.png
[widget-opacity]: https://raw.githubusercontent.com/antoineedy/istacky/main/docs/img/widgets/opacity.png
[widget-reset]: https://raw.githubusercontent.com/antoineedy/istacky/main/docs/img/widgets/reset.png
[widget-show]: https://raw.githubusercontent.com/antoineedy/istacky/main/docs/img/widgets/show.png
[widget-add-image]: https://raw.githubusercontent.com/antoineedy/istacky/main/docs/img/widgets/add_image.png
[widget-scale]: https://raw.githubusercontent.com/antoineedy/istacky/main/docs/img/widgets/scale.png
[widget-x]: https://raw.githubusercontent.com/antoineedy/istacky/main/docs/img/widgets/x.png
[widget-y]: https://raw.githubusercontent.com/antoineedy/istacky/main/docs/img/widgets/y.png
[widget-copy]: https://raw.githubusercontent.com/antoineedy/istacky/main/docs/img/widgets/copy.png
[widget-threshold]: https://raw.githubusercontent.com/antoineedy/istacky/main/docs/img/widgets/threshold.png
[widget-visualize]: https://raw.githubusercontent.com/antoineedy/istacky/main/docs/img/widgets/visualize.png
