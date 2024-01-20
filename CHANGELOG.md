### 20/01/2024 (not released)
---
* Bug corrections:
    * Background cropping in the `code`: the code generated from the editor mode was not working properly, as cropping the background would lead to some position issues on all of the layers.
    * Background cropping was not updated in the GUI when using a `code`.
    * Background cropping is is pixel and did not translate well when using a `code` with a different resolution than the background.

* Changes:
    * When expanding the background (in any of the four directions), the newly generated part of the background is now white instead of black (which leads to better aesthetic results when adding plots!).
    * Ignore some warnings from `pillow` when they are not relevant to the user.


### 19/01/2024 (v.0.1.0)
---
Initial PyPi release!

### 25/12/2023
---
Very beggining of the project