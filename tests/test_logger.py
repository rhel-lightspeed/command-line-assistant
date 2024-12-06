import logging


def test_verbose_logging(caplog):
    log = logging.getLogger()

    log.info("test")

    assert "test" in caplog.records[-1].message
