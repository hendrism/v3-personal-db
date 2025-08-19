import inspect


class BaseModel:
    """Base model with common functionality."""

    @classmethod
    def get_by_id(cls, db, id):
        cursor = db.execute(f"SELECT * FROM {cls.table_name} WHERE id = ?", (id,))
        row = cursor.fetchone()
        return cls.from_row(row) if row else None

    @classmethod
    def from_row(cls, row):
        """Create instance from database row.
        Filters out unexpected keys so JOINed columns don't break constructors.
        Also attaches any extra columns to the instance as attributes.
        """
        if not row:
            return None
        data = dict(row)
        allowed = cls._allowed_fields()
        filtered = {k: v for k, v in data.items() if k in allowed}
        inst = cls(**filtered)
        # Attach any extra columns so callers can still access them if needed
        for k, v in data.items():
            if k not in allowed:
                setattr(inst, k, v)
        return inst

    @classmethod
    def _allowed_fields(cls):
        """Return constructor argument names (excluding 'self')."""
        sig = inspect.signature(cls.__init__)
        # Keep parameters that can be passed as kwargs
        names = [p.name for p in sig.parameters.values() if p.name != 'self']
        return set(names)

    def to_dict(self):
        """Convert to dictionary."""
        return {k: v for k, v in self.__dict__.items()
                if not k.startswith('_')}
