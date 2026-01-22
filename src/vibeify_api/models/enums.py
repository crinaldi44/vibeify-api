from enum import Enum


class DocumentType(str, Enum):
    REPORT = "report"
    USER_UPLOAD = "upload"

class NotificationType(str, Enum):
    GENERAL = "general"
    DOCUMENT_UPLOAD = "upload-complete"
    REPORT_GENERATION = "report-generation"

class ReviewItemType(str, Enum):
    GENERAL = "general"

class RoleType(str, Enum):
    USER = "User"
    ADMIN = "Administrator"
