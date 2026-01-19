from typing import Optional
import aioboto3

_s3_session: Optional[aioboto3.Session] = None


def get_s3_session() -> aioboto3.Session:
    """Get or create singleton S3 session.
    
    Returns:
        aioboto3.Session instance
    """
    global _s3_session
    if _s3_session is None:
        _s3_session = aioboto3.Session()
    return _s3_session