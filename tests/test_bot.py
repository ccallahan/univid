from univid.bot import status_text


def test_status_text():
    assert status_text(0) == "0 videos embedded since restart"
    assert status_text(1) == "1 video embedded since restart"
    assert status_text(5) == "5 videos embedded since restart"
