# w3-weather-stills (draft, 2.W3 §a; owed L4)

**Checks:** the 4 Black Marsh weathers of ours and the restyled Tropical Skyrim weathers read as humid green-gold
marsh light, with no Nordic blue-grey. A reader panel judges 12 stills against the old weather references.

- **Scene:** the base save, one open marsh view (a lagoon edge in a marsh region) and one jungle view. Step 0 sets
  the camera, the time and the weather (`fw <WTHR>`). Forcing the weather sets the thing under test only for the look;
  the cycling is w3-weather-skip's job.
- **Stills (12):** mist at 06:00 and 18:00; tannin haze at 12:00; storm at 15:00 and 22:00; squall on the coast at
  12:00; Tropical Skyrim's clear, cloudy, rain and fog at 12:00 in each view, to make 12. All at the play camera.
- **Reader:** the Nordic-tells checklist (blue-grey fog, snow light, pale sun) plus an open judgement against the old
  weather references. A still fails on a tell.
- **Loop:** the lane edits the weather and image-space rows (`weather`, `image_space`) or `regions/api.py`'s LADDER,
  then rebuilds and re-shoots. It stops when the panel passes or after 3 passes with a written reason. The final look
  is 4.6's.
- **Fails if:** a black or white sky (a colour slot left at zero), missing clouds (a template's cloud paths not
  carried), a crash.
