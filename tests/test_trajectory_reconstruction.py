import numpy as np
from trajectory_reconstruction import reconstruct


def track(values):
    return np.array([[[v,0]] if v is not None else [[np.nan,np.nan]] for v in values],float)


def test_jump_is_not_promoted_to_location():
    x=track([0,1,2,500,4,5,6])
    r=reconstruct(x)
    assert r['rejected'][3,0]
    assert r['held'][3,0,0]==2
    assert r['accepted'][4,0]
    np.testing.assert_equal(r['raw'],x)


def test_long_gap_allows_distance_but_holds_until_return():
    r=reconstruct(track([0,1,2,None,None,None,302,303,304]))
    assert r['accepted'][6,0]
    assert (r['held'][3:6,0,0]==2).all()
    assert (r['bridge'][3:6,0,0]==[77,152,227]).all()


def test_two_frame_gap_still_has_speed_limit():
    r=reconstruct(track([0,1,2,None,303,304,305]))
    assert not r['accepted'][4,0]  # 301 px in two intervals


def test_no_fake_initial_or_terminal_positions():
    r=reconstruct(track([None,0,1,2,None,20]))
    assert np.isnan(r['held'][0]).all()
    assert not r['accepted'][-1,0]
    assert np.isnan(r['bridge'][-1]).all()


def test_exact_limit_and_stationary_valid():
    r=reconstruct(track([0,100,200,200]))
    assert r['accepted'].all()
