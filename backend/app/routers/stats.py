from app.database import get_repository
from fastapi import APIRouter, Depends

router = APIRouter(prefix="/stats", tags=["stats"])


@router.get("/{usuario_id}")
async def obtener_estadisticas(usuario_id: str, repository=Depends(get_repository)):
    stats = await repository.get_stats(usuario_id)

    if not stats:
        return {
            "partidas_jugadas": 0,
            "partidas_ganadas": 0,
            "racha_actual": 0,
            "racha_maxima": 0,
            "porcentaje_victorias": 0
        }

    s = stats
    porcentaje = round((s["partidas_ganadas"] / s["partidas_jugadas"]) * 100) if s["partidas_jugadas"] > 0 else 0

    return {**s, "porcentaje_victorias": porcentaje}


@router.get("/ranking/global")
async def ranking_global(repository=Depends(get_repository)):
    stats = await repository.ranking()

    return {"ranking": stats}