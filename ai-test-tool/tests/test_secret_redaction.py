from ai_test_tool import secret_redaction


def test_redacts_aws_access_key_id():
    source = 'AWS_KEY = "AKIAABCDEFGHIJKLMNOP"\n'
    redacted, changed = secret_redaction.redact(source)
    assert changed is True
    assert "AKIAABCDEFGHIJKLMNOP" not in redacted
    assert "[REDACTED]" in redacted


def test_redacts_pem_private_key_block():
    source = (
        "KEY = '''\n-----BEGIN RSA PRIVATE KEY-----\n"
        "MIIEowIBAAKCAQEA1234567890abcdef\n"
        "-----END RSA PRIVATE KEY-----\n'''\n"
    )
    redacted, changed = secret_redaction.redact(source)
    assert changed is True
    assert "MIIEowIBAAKCAQEA1234567890abcdef" not in redacted


def test_redacts_bearer_token():
    source = 'headers = {"Authorization": "Bearer sk-abc123def456ghi789"}\n'
    redacted, changed = secret_redaction.redact(source)
    assert changed is True
    assert "sk-abc123def456ghi789" not in redacted
    assert "Bearer" in redacted


def test_redacts_api_key_assignment_keeps_variable_name():
    source = 'api_key = "sk-live-abcdef123456"\n'
    redacted, changed = secret_redaction.redact(source)
    assert changed is True
    assert "sk-live-abcdef123456" not in redacted
    assert "api_key" in redacted


def test_redacts_password_assignment():
    source = "password: str = 'hunter2hunter2'\n"
    redacted, changed = secret_redaction.redact(source)
    assert changed is True
    assert "hunter2hunter2" not in redacted


def test_does_not_flag_ordinary_code():
    source = (
        "def trips_overlap(start_a, end_a, start_b, end_b):\n"
        "    return start_a <= end_b and start_b <= end_a\n"
    )
    redacted, changed = secret_redaction.redact(source)
    assert changed is False
    assert redacted == source


def test_does_not_flag_short_unrelated_strings():
    # Guards against the assignment pattern being so broad it flags every
    # short quoted string in ordinary code.
    source = 'status = "ok"\ncolor = "red"\n'
    redacted, changed = secret_redaction.redact(source)
    assert changed is False
    assert redacted == source


def test_redacts_multiple_secrets_in_one_source():
    source = 'api_key = "abcdef123456"\npassword = "hunter2hunter2"\n'
    redacted, changed = secret_redaction.redact(source)
    assert changed is True
    assert "abcdef123456" not in redacted
    assert "hunter2hunter2" not in redacted
