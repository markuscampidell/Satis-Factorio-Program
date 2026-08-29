# objects.item_filter
class ItemFilter:
    """A togglable whitelist bound to a fixed number of selection slots -
    each slot is either empty (None) or holds one item_id. Shared by
    BeltSegment (one filter per tile) and Splitter (one per output side).
    When disabled, everything is accepted; when enabled, only items sitting
    in a slot are - an enabled filter with every slot still empty blocks
    everything rather than passing everything through.

    SLOT_COUNT is a fixed constant rather than len(constants.itemdata.ITEMS)
    so this module stays free of any dependency on the item roster - bump
    it by hand if the item list ever grows past it."""

    SLOT_COUNT = 10

    def __init__(self):
        self.enabled = False
        self.slots = [None] * self.SLOT_COUNT

    def accepts(self, item_id):
        return not self.enabled or item_id in self.slots

    def set_slot(self, index, item_id):
        self.slots[index] = item_id

    def clear_slot(self, index):
        self.slots[index] = None

    def to_dict(self):
        return {"enabled": self.enabled, "slots": list(self.slots)}

    @classmethod
    def from_dict(cls, data):
        f = cls()
        f.enabled = data.get("enabled", False)

        if "slots" in data:
            slots = data["slots"]
            for i in range(min(len(slots), f.SLOT_COUNT)):
                f.slots[i] = slots[i]
        else:
            # Back-compat with the pre-slots filter format (a flat
            # allowed_items list, unordered) - drop items into slots in
            # whatever order they were stored.
            legacy_items = data.get("allowed_items", [])
            for i, item_id in enumerate(legacy_items[:f.SLOT_COUNT]):
                f.slots[i] = item_id

        return f
