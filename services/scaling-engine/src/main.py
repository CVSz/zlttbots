from typing import Any

import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel, Field

app = FastAPI(title="Scaling Engine")


class ScaleRequest(BaseModel):
    campaign_id: str = Field(min_length=1)
    score: float = Field(ge=0.0)


class ScaleResponse(BaseModel):
    campaign_id: str
    action: str
    factor: float


@app.get("/healthz")
def healthz() -> dict[str, Any]:
    return {"status": "ok", "service": "scaling-engine"}


@app.post("/scale", response_model=ScaleResponse)
def scale(request: ScaleRequest) -> ScaleResponse:
    if request.score >= 0.2:
        action = "scale_up"
        factor = min(5.0, 1.0 + (request.score * 10.0))
    elif request.score <= 0.05:
        action = "scale_down"
        factor = max(0.2, request.score * 10.0)
    else:
        action = "hold"
        factor = 1.0

    return ScaleResponse(campaign_id=request.campaign_id, action=action, factor=round(factor, 4))


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
