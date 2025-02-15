import show


def test_ellipsis():
    value = "scripts-0.1.0-py3-none-any.whl"
    assert show.ellipsis(value) == value

    value = "202501_6845530474_20250213130948.pdf"
    e = show.ellipsis(value)
    assert e == "202501_68455304(...)130948.pdf"
    assert len(e) == 30

    value = "webp-pixbuf-loader_0.0.4-0~202205152028+202205152231~ubuntu20.04.1_amd64.deb"
    e = show.ellipsis(value)
    assert e == "webp-pixbuf-loa(...)_amd64.deb"
    assert len(e) == 30

    value = "1895626515220692901356254961528463709728e700ccabb61529331309.jpg"
    e = show.ellipsis(value)
    assert e == "189562651522069(...)331309.jpg"
    assert len(e) == 30

    value = "There should be one and preferably only one obvious way to do it.pdf"
    e = show.ellipsis(value)
    assert e == "There should be(...) do it.pdf"
    assert len(e) == 30
