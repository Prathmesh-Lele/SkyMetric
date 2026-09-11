"""FastAPI application entry point with endpoint registration."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from skymetric.api.routes.index import router as index_router
from skymetric.api.routes.heatmap import router as heatmap_router
from skymetric.api.routes.elasticity import router as elasticity_router
from skymetric.api.routes.scraper import router as scraper_router

app = FastAPI(
    title="SkyMetric - India Airfare Price Index",
    description="Real-time airfare price index for Indian domestic corridors",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(index_router, prefix="/api/v1/index", tags=["Index"])
app.include_router(heatmap_router, prefix="/api/v1/routes", tags=["Heatmap"])
app.include_router(elasticity_router, prefix="/api/v1/elasticity", tags=["Elasticity"])
app.include_router(scraper_router, prefix="/api/v1/scraper", tags=["Scraper"])


@app.get("/api/v1/health", tags=["Health"])
def health_check():
    return {"status": "healthy", "service": "skymetric"}
