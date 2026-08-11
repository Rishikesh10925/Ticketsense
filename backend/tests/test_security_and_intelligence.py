from app.services.ticket_intelligence import redact


def test_redacts_external_pii():
    clean, kinds = redact("Contact jane@example.com and password: SuperSecret123")
    assert "jane@example.com" not in clean
    assert "SuperSecret123" not in clean
    assert set(kinds) == {"email", "secret"}


def test_non_sensitive_text_is_unchanged():
    source = "VPN authentication fails after MFA reset"
    clean, kinds = redact(source)
    assert clean == source
    assert kinds == []
