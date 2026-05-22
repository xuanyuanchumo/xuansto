from datetime import datetime
from typing import Optional, List, Any
from sqlalchemy.orm.attributes import flag_modified


class StatusHistoryManager:
    @staticmethod
    def add_status_history(
        entity: Any,
        from_status: str,
        to_status: str,
        operator: Optional[str],
        comment: Optional[str]
    ) -> None:
        history = entity.status_history or []
        history.append({
            "from_status": from_status,
            "to_status": to_status,
            "operator": operator,
            "comment": comment,
            "timestamp": datetime.now().isoformat()
        })
        entity.status_history = history
        flag_modified(entity, 'status_history')

    @staticmethod
    def get_status_history(entity: Any) -> List[dict]:
        return entity.status_history or []
