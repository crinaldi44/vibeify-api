from enum import Enum


class DocumentType(str, Enum):
    REPORT = "report"
    USER_UPLOAD = "upload"