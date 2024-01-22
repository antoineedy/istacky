# :chart_with_upwards_trend: Changelog
_To keep track of the changes made to the project, this changelog is updated (at least!) with each new release._

---
#### 21/01/2024 (v.0.1.2)
* Bug corrections:
    * Cropping the background on the top or the left led to a wrong coloration of the rest of the images.

---
#### 20/01/2024 (v.0.1.1)
* Bug corrections:
    * Background cropping in the `code`: the code generated from the editor mode was not working properly, as cropping the background would lead to some position issues on all of the layers.
    * Background cropping was not updated in the GUI when using a `code`.
    * Background cropping is is pixel and did not translate well when using a `code` with a different resolution than the background.

* Changes:
    * When expanding the background (in any of the four directions), the newly generated part of the background is now white instead of black (which leads to better aesthetic results when adding plots!).
    * Ignore some warnings from `pillow` when they are not relevant to the user.

---
#### 19/01/2024 (v.0.1.0)
Initial PyPi release!

---
#### 25/12/2023
Very beginning of the project.