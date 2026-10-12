from app.database import get_supabase
from fastapi import APIRouter, Depends

router = APIRouter(prefix="/stats", tags=["stats"])


@router.get("/{usuario_id}")
async def obtener_estadisticas(usuario_id: str, supabase=Depends(get_supabase)):
    stats = supabase.table("estadisticas") \
        .select("*") \
        .eq("usuario_id", usuario_id) \
        .execute()

    if not stats.data:
        return {
            "partidas_jugadas": 0,
            "partidas_ganadas": 0,
            "racha_actual": 0,
            "racha_maxima": 0,
            "porcentaje_victorias": 0
        }

    s = stats.data[0]
    porcentaje = round((s["partidas_ganadas"] / s["partidas_jugadas"]) * 100) if s["partidas_jugadas"] > 0 else 0

    return {**s, "porcentaje_victorias": porcentaje}


@router.get("/ranking/global")
async def ranking_global(supabase=Depends(get_supabase)):
    stats = supabase.table("estadisticas") \
        .select("usuario_id, partidas_ganadas, racha_maxima, partidas_jugadas") \
        .order("partidas_ganadas", desc=True) \
        .limit(10) \
        .execute()

    return {"ranking": stats.data}