from uuid import UUID

type EntityID = int | str | UUID | dict[str, EntityID]
