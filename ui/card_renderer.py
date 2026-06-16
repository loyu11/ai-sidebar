import json

from storage.models import Item


class CardRenderer:
    @staticmethod
    def items_to_json(items: list[Item]) -> str:
        return json.dumps(
            [item.to_dict() for item in items],
            ensure_ascii=False,
        )
