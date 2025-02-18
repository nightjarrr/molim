from molim import show


def test_ellipsis():
    value = "scripts-0.1.0-py3-none-any.whl"
    assert show.ellipsis(value) == value

    value = "202501_6845530474_20250213130948.pdf"
    e = show.ellipsis(value)
    assert e == "202501_6845530474_20250213130948.pdf"

    value = "webp-pixbuf-loader_0.0.4-0~202205152028+202205152231~ubuntu20.04.1_amd64.deb"
    e = show.ellipsis(value)
    assert e == "webp-pixbuf-loader_0.0.4-0(...)_amd64.deb"
    assert len(e) == 41

    value = "1895626515220692901356254961528463709728e700ccabb61529331309.jpg"
    e = show.ellipsis(value)
    assert e == "18956265152206929013562549(...)331309.jpg"
    assert len(e) == 41

    value = "There should be one and preferably only one obvious way to do it.pdf"
    e = show.ellipsis(value)
    assert e == "There should be one and pr(...) do it.pdf"
    assert len(e) == 41


def test_human_size():
    assert show.human_size(10) == "10"
    assert show.human_size(1024) == "1.0K"
    assert show.human_size(3.4 * 1024 * 1024) == "3.4M"
    assert show.human_size(8.9 * 1024 * 1024 * 1024) == "8.9G"
    assert show.human_size(6.034 * 1024 * 1024 * 1024 * 1024) == "6.0T"
    assert show.human_size(5247.68 * 1024 * 1024 * 1024 * 1024) == "5247.7T"
