import logging
import json
from .config import settings

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_record = {
            "level": record.levelname,
            "message": record.getMessage(),
            "timestamp": self.formatTime(record),
            "name": record.name,
            "filename": record.filename,
            "lineno": record.lineno,
            "funcName": record.funcName
        }
        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_record)

def setup_logging():
    log_level = settings.LOG_LEVEL.upper()
    logging.basicConfig(level=log_level, format="%(message)s")
    
    logger = logging.getLogger("uvicorn.access")
    logger.handlers = []
    handler = logging.StreamHandler()
    handler.setFormatter(JSONFormatter())
    logger.addHandler(handler)
    logger.setLevel(log_level)
    
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    for handler in root_logger.handlers:
        handler.setFormatter(JSONFormatter())

setup_logging()
logger = logging.getLogger(__name__)
