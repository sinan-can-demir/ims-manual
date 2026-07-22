from pydantic import BaseModel, Field

# event_type and quantity are kept loose (not EventType/validated int) at
# this outer-payload level on purpose — strict per-row validation happens
# inside ingestion_service.ingest_events (via IngestRowInput), so one
# malformed event in a batch is reported as a per-row failure alongside
# the rest, instead of failing Pydantic validation for the whole payload.


class WebhookEventItem(BaseModel):
    sku: str = Field(min_length=1, max_length=100)
    event_type: str
    quantity: int
    external_id: str = Field(min_length=1, max_length=100)


class WebhookIngestPayload(BaseModel):
    source: str = Field(min_length=1, max_length=50)
    events: list[WebhookEventItem]
