from pydantic import BaseModel


class ExportMetadata(BaseModel):
    rows_exported: int
    partitions_written: int
    files_written: int
    mode: str
    checkpoint_updated: bool
