"""The look audit's judgement of one sampled piece (tools/places/look/truth_sample.py `judged`)."""
from tools.places.look.truth_sample import judged


def test_a_piece_drawn_off_its_box_fails_and_one_on_it_passes():
    assert judged(0.0, 1.0, 0.01, 0.6)
    assert not judged(0.05, 1.0, 0.01, 0.6)          # pixels outside the box: a wrong transform or model
    assert not judged(0.0, 1.0, 0.09, 0.6)           # a full silhouette off its box's centre


def test_a_sparse_alpha_cut_plant_inside_its_box_is_not_failed_for_its_centre():
    assert judged(0.0, 0.95, 0.09, 0.1)              # hanging moss: every pixel inside, the quads mostly see-through
    assert not judged(0.005, 0.95, 0.09, 0.1)        # a pixel outside the box still counts against it
