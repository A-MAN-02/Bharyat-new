from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import vendors, rfq, dispatch, responses, scorecard, award, vendor_registration

app = FastAPI(title="QProcure API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # tighten this before production
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(vendors.router)
app.include_router(rfq.router)
app.include_router(dispatch.router)
app.include_router(responses.router)
app.include_router(scorecard.router)
app.include_router(award.router)
app.include_router(vendor_registration.router)


@app.get("/")
def health_check():
    return {"status": "QProcure API running"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8002, reload=True)