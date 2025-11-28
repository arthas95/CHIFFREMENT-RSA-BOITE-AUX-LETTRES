from fastapi import APIRouter
import httpx

router = APIRouter(prefix="/gold", tags=["Gold"])

API_KEY = "goldapi-4uq3smi6sd2q9-io"

@router.get("/ounce")
async def gold_ounce_only():
    headers = {"x-access-token": API_KEY}

    async with httpx.AsyncClient() as client:
        r = await client.get(
            "https://www.goldapi.io/api/XAU/EUR",
            headers=headers
        )
        data = r.json()
        return {"price_ounce_eur": data["price"]}