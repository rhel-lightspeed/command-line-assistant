from command_line_assistant.config.schemas.backend import AuthSchema


# TODO(r0x0d): Once we remove the depreaction notice, remove this as well.
def test_verify_ssl_deprecation_notice(caplog):
    _ = AuthSchema(verify_ssl=True)
    assert (
        "Verify SSL option is deprecated and will be removed in the future."
        in caplog.records[-2].message
    )
    assert (
        "Ignoring Verify SSL option as it has no effect anymore."
        in caplog.records[-1].message
    )
