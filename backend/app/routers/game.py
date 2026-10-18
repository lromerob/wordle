import random

from app.database import get_supabase
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/game", tags=["game"])

MAX_INTENTOS = 6
LONGITUD_PALABRA = 5


class IntentoPeticion(BaseModel):
    partida_id: str
    palabra: str
    usuario_id: str


def evaluar_intento(palabra_secreta: str, intento: str) -> list[dict]:
    resultado = [{"letra": l, "estado": "ausente"} for l in intento]
    conteo_secreta = {}

    for i, (s, i_letra) in enumerate(zip(palabra_secreta, intento)):
        if s == i_letra:
            resultado[i]["estado"] = "correcto"
        else:
            conteo_secreta[s] = conteo_secreta.get(s, 0) + 1

    for i, (s, i_letra) in enumerate(zip(palabra_secreta, intento)):
        if resultado[i]["estado"] != "correcto" and i_letra in conteo_secreta and conteo_secreta[i_letra] > 0:
            resultado[i]["estado"] = "presente"
            conteo_secreta[i_letra] -= 1

    return resultado


@router.post("/nueva")
async def nueva_partida(usuario_id: str, supabase=Depends(get_supabase)):
    palabra = supabase.table("palabras").select("palabra").execute()

    if not palabra.data:
        raise HTTPException(status_code=500, detail="No hay palabras disponibles")

    palabra_elegida = random.choice(palabra.data)["palabra"].upper()

    partida = supabase.table("partidas").insert({
        "usuario_id": usuario_id,
        "palabra_secreta": palabra_elegida,
        "intentos_usados": 0,
        "estado": "en_curso"
    }).execute()

    return {"partida_id": partida.data[0]["id"]}


@router.post("/intento")
async def registrar_intento(body: IntentoPeticion, supabase=Depends(get_supabase)):
    palabra = body.palabra.strip()
    # Validate before upper(): Unicode case expansion can change word length.
    if len(palabra) != LONGITUD_PALABRA or any(
        letra not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZñÑ"
        for letra in palabra
    ):
        raise HTTPException(status_code=400, detail="La palabra debe tener 5 letras de A a Z o Ñ")
    intento = palabra.upper()

    partida = supabase.table("partidas").select("*").eq("id", body.partida_id).limit(1).execute()

    if not partida.data:
        raise HTTPException(status_code=404, detail="Partida no encontrada")

    p = partida.data[0]
    # Consistency check only: usuario_id is unverified until authentication exists.
    if p["usuario_id"] != body.usuario_id:
        raise HTTPException(status_code=403, detail="El usuario no coincide con la partida")
    if p["estado"] != "en_curso":
        raise HTTPException(status_code=400, detail=f"La partida ya terminó: {p['estado']}")

    if p["intentos_usados"] >= MAX_INTENTOS:
        raise HTTPException(status_code=400, detail="No quedan intentos")

    palabra_valida = supabase.table("palabras").select("palabra").eq("palabra", intento).execute()

    if not palabra_valida.data:
        raise HTTPException(status_code=400, detail="Palabra no válida")

    resultado = evaluar_intento(p["palabra_secreta"], intento)
    gano = all(r["estado"] == "correcto" for r in resultado)
    nuevo_intento = p["intentos_usados"] + 1
    nuevo_estado = "ganada" if gano else ("perdida" if nuevo_intento >= MAX_INTENTOS else "en_curso")

    supabase.table("intentos").insert({
        "partida_id": body.partida_id,
        "usuario_id": body.usuario_id,
        "numero": nuevo_intento,
        "palabra": intento,
        "resultado": resultado
    }).execute()

    supabase.table("partidas").update({
        "intentos_usados": nuevo_intento,
        "estado": nuevo_estado
    }).eq("id", body.partida_id).execute()

    if nuevo_estado in ("ganada", "perdida"):
        _actualizar_estadisticas(p["usuario_id"], nuevo_estado == "ganada", nuevo_intento, supabase)

    return {
        "resultado": resultado,
        "estado": nuevo_estado,
        "intentos_usados": nuevo_intento,
        "palabra_secreta": p["palabra_secreta"] if nuevo_estado == "perdida" else None
    }


@router.get("/{partida_id}")
async def estado_partida(partida_id: str, supabase=Depends(get_supabase)):
    partida = supabase.table("partidas").select("*").eq("id", partida_id).limit(1).execute()

    if not partida.data:
        raise HTTPException(status_code=404, detail="Partida no encontrada")

    intentos = supabase.table("intentos").select("*").eq("partida_id", partida_id).order("numero").execute()

    public_partida = dict(partida.data[0])
    if public_partida.get("estado") not in ("ganada", "perdida"):
        public_partida.pop("palabra_secreta", None)
    return {"partida": public_partida, "intentos": intentos.data}


def _actualizar_estadisticas(usuario_id: str, gano: bool, intentos: int, supabase):
    stats = supabase.table("estadisticas").select("*").eq("usuario_id", usuario_id).execute()

    if not stats.data:
        supabase.table("estadisticas").insert({
            "usuario_id": usuario_id,
            "partidas_jugadas": 1,
            "partidas_ganadas": 1 if gano else 0,
            "racha_actual": 1 if gano else 0,
            "racha_maxima": 1 if gano else 0,
            "intentos_promedio": intentos if gano else 0
        }).execute()
    else:
        s = stats.data[0]
        nueva_racha = (s["racha_actual"] + 1) if gano else 0
        supabase.table("estadisticas").update({
            "partidas_jugadas": s["partidas_jugadas"] + 1,
            "partidas_ganadas": s["partidas_ganadas"] + (1 if gano else 0),
            "intentos_promedio": (
                ((s.get("intentos_promedio") or 0) * s["partidas_ganadas"] + intentos)
                / (s["partidas_ganadas"] + 1)
                if gano else (s.get("intentos_promedio") or 0)
            ),
            "racha_actual": nueva_racha,
            "racha_maxima": max(s["racha_maxima"], nueva_racha),
        }).eq("usuario_id", usuario_id).execute()