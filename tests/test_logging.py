import logging

from command_line_assistant import config, logger


def test_write_to_logfile(tmp_path):
    tmp_log_file = tmp_path / "cla" / "cla.log"
    logger.setup_logging(config.Config(logging=config.LoggingSchema(file=tmp_log_file)))
    log = logging.getLogger()

    log.info("test")

    assert tmp_log_file.exists()
    assert "INFO: test" in tmp_log_file.read_text()


def test_verbose_logging(caplog):
    log = logging.getLogger()

    log.info("test")

    assert "test" in caplog.records[-1].message
