import logging

from asgi_correlation_id import CorrelationIdFilter
from pythonjsonlogger import jsonlogger


def configure_logging():
    logger = logging.getLogger()
    logHandler = logging.StreamHandler()
    
    # JSON formatter
    formatter = jsonlogger.JsonFormatter(
        "%(asctime)s %(levelname)s %(name)s %(message)s %(correlation_id)s",
        rename_fields={"levelname": "severity", "asctime": "timestamp"}
    )
    logHandler.setFormatter(formatter)
    
    # Correlation ID filter
    logHandler.addFilter(CorrelationIdFilter())
    
    logger.handlers = [logHandler]
    logger.setLevel(logging.INFO)
    
    # Silence noisy libs
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
