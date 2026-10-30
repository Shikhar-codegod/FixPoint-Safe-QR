from .models import OperationsLogEntry

def add_ops_log(operator, action: str, incident=None, details: str = '') -> OperationsLogEntry:
    return OperationsLogEntry.objects.create(
        operator=operator,
        incident=incident,
        action=action,
        details=details
    )
