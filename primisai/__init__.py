import logging as _logging

__version__ = "1.0.0"

_logger = _logging.getLogger("primisai")
if not _logger.handlers:
    _handler = _logging.StreamHandler()
    _handler.setFormatter(
        _logging.Formatter("%(name)s — %(levelname)s — %(message)s")
    )
    _logger.addHandler(_handler)
    if _logger.level == _logging.NOTSET:
        _logger.setLevel(_logging.INFO)
    # Make sure sub-loggers (e.g. "primisai.nexus.core.supervisor") propagate
    # up to this handler instead of being lost.
    _logger.propagate = False
del _handler
del _logger
del _logging
