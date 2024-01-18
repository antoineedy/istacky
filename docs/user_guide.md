<a name="top-of-the-page"></a>

## Installation

#### Using pip
```sh
pip install istacky # not working yet!
```

#### Install and run from source code

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

#### :video_camera: Video tutorial (coming soon)

!!! quote ""
    === "English version"
        <iframe width="560" height="315" src="https://www.youtube.com/embed/U3erapTSOeQ?si=WQbar1MTokNdB-dT" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" allowfullscreen></iframe>

    === "French version"
        <iframe width="560" height="315" src="https://www.youtube.com/embed/U3erapTSOeQ?si=WQbar1MTokNdB-dT" title="YouTube video player" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" allowfullscreen></iframe>

#### :notebook: Example

Import the libraries needed:
```python
from PIL import Image
import istacky
```

Load the images we want to stack:
```python
background = Image.open("image/background.png")
img1 = Image.open("image/img1.png")
img2 = Image.open("image/img2.png")
```

Create a `BlendedImage` object and display it:
```python
blended = istacky.BlendedImage(background, [img1, img2])
blended.show()
```
![First output](/img/output_bad.png "Title")

The images are just stacked on top of each other! Let's apply some modifications to them:
```python
blended.editor()
```
![Editor](/img/editor.png "Title")

Calling editor displays a widget that allows you to apply modifications to the images. You can crop, resize, change the opacity, remove the background, add images, change the orders of the layers etc. 

In our case, we want to put the logo in one corner, circle the pisition of the ball and add a plot of the trajectory of the ball. After the changes, here is the final result:

```python
blended.show()
```
![Final output](/img/output_good.png "Title")

Now, if we want to apply the same modifications to another image, we can have access to the code that was used to create the final image, and apply it to another one:
```python
my_code = blended.get_code()
```
We will use the same background, but different images:
```python
new_img1 = Image.open("image/new_img1.png")
new_img2 = Image.open("image/new_img2.png")
new_img3 = Image.open("image/new_img3.png")
``` 
We specify the code that was used to create the first image, and apply it to the new images:
```python
new_blended = istacky.BlendedImage(
    background=background,
    images = [new_img1, new_img2, new_img3],
    code=my_code
    )
    
new_blended.show()
```
![Final output](/img/output_good2.png "Title")

We can see that the modifications have been applied to the new images!