from app.security import check_body, check_link, sign_body, sign_link


def test_body_signature():
    sig = sign_body(b"k", b"{}")
    assert check_body(b"k", b"{}", sig)
    assert not check_body(b"k", b"{ }", sig)
    assert not check_body(b"k", b"{}", "")


def test_link_purpose_is_bound():
    sig = sign_link(b"k", "receipt", "pay_1")
    assert check_link(b"k", "receipt", "pay_1", sig)
    assert not check_link(b"k", "verify", "pay_1", sig)
    assert not check_link(b"k", "receipt", "pay_2", sig)
