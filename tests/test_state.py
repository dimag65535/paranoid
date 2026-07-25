from slot_watch.state import WatchState, load_state, save_state


def test_state_round_trip(tmp_path) -> None:
    path = tmp_path / "nested" / "state.json"
    expected = WatchState(
        available=True,
        checked_at="2026-07-25T10:00:00+00:00",
        last_error=None,
    )
    save_state(path, expected)
    assert load_state(path) == expected


def test_missing_or_invalid_state_is_clean(tmp_path) -> None:
    path = tmp_path / "state.json"
    assert load_state(path) == WatchState()
    path.write_text("not json", encoding="utf-8")
    assert load_state(path) == WatchState()
