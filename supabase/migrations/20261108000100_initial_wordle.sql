-- FIN-01B: structure reported by owner on 2026-11-08, not a live export.
-- Apply ONCE to a NEW, explicitly authorized disposable local database only.
-- PostgreSQL 16 test target; gen_random_uuid() is built in (no extension added).
-- public must already exist. No roles, RLS, grants, seeds or extra constraints.
-- Sequence settings and constraint names were not supplied; see README.
BEGIN;

CREATE SEQUENCE public.palabras_id_seq;

CREATE TABLE public.palabras (
    id integer NOT NULL DEFAULT nextval('public.palabras_id_seq'::regclass),
    palabra character varying NOT NULL,
    PRIMARY KEY (id),
    UNIQUE (palabra)
);

CREATE TABLE public.partidas (
    id uuid NOT NULL DEFAULT gen_random_uuid(),
    usuario_id text NOT NULL,
    palabra_secreta character varying NOT NULL,
    intentos_usados integer DEFAULT 0,
    estado character varying DEFAULT 'en_curso',
    created_at timestamp without time zone DEFAULT now(),
    PRIMARY KEY (id)
);

CREATE TABLE public.intentos (
    id uuid NOT NULL DEFAULT gen_random_uuid(),
    partida_id uuid,
    usuario_id text NOT NULL,
    numero integer NOT NULL,
    palabra character varying NOT NULL,
    resultado jsonb NOT NULL,
    created_at timestamp without time zone DEFAULT now(),
    PRIMARY KEY (id),
    FOREIGN KEY (partida_id) REFERENCES public.partidas (id)
);

CREATE TABLE public.estadisticas (
    id uuid NOT NULL DEFAULT gen_random_uuid(),
    usuario_id text NOT NULL,
    partidas_jugadas integer DEFAULT 0,
    partidas_ganadas integer DEFAULT 0,
    racha_actual integer DEFAULT 0,
    racha_maxima integer DEFAULT 0,
    intentos_promedio numeric DEFAULT 0,
    updated_at timestamp without time zone DEFAULT now(),
    PRIMARY KEY (id),
    UNIQUE (usuario_id)
);

COMMIT;
