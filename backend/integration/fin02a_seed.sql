-- Synthetic FIN-02A only. Never part of initdb/runtime. Run through the opt-in runner.
BEGIN;
DO $guard$ BEGIN
 IF current_setting('wordle.synthetic_seed', true) IS DISTINCT FROM 'authorized-disposable'
    OR current_database() !~ '^fin02[ab]_[0-9a-f]{12}$' THEN
  RAISE EXCEPTION 'Synthetic seed requires explicitly authorized disposable FIN-02 database';
 END IF;
END $guard$;
LOCK TABLE public.palabras, public.partidas, public.intentos, public.estadisticas IN SHARE ROW EXCLUSIVE MODE;
CREATE TEMP TABLE expected_games (LIKE public.partidas) ON COMMIT DROP;
CREATE TEMP TABLE expected_attempts (LIKE public.intentos) ON COMMIT DROP;
CREATE TEMP TABLE expected_stats (LIKE public.estadisticas) ON COMMIT DROP;
INSERT INTO expected_games VALUES
('f102a000-0000-4000-8000-000000000001','fin02a-demo','CASAS',1,'ganada','2026-01-01 12:00:00'),
('f102a000-0000-4000-8000-000000000002','fin02a-demo','CASAS',6,'perdida','2026-01-02 12:00:00'),
('f102a000-0000-4000-8000-000000000003','fin02a-demo','CASAS',1,'en_curso','2026-01-03 12:00:00');
INSERT INTO expected_attempts VALUES
('f102a000-0000-4000-8000-000000000101','f102a000-0000-4000-8000-000000000001','fin02a-demo',1,'CASAS','[{"letra": "C", "estado": "correcto"}, {"letra": "A", "estado": "correcto"}, {"letra": "S", "estado": "correcto"}, {"letra": "A", "estado": "correcto"}, {"letra": "S", "estado": "correcto"}]'::jsonb,'2026-01-01 12:00:00'),
('f102a000-0000-4000-8000-000000000201','f102a000-0000-4000-8000-000000000002','fin02a-demo',1,'PERRO','[{"letra": "P", "estado": "ausente"}, {"letra": "E", "estado": "ausente"}, {"letra": "R", "estado": "ausente"}, {"letra": "R", "estado": "ausente"}, {"letra": "O", "estado": "ausente"}]'::jsonb,'2026-01-02 12:00:00'),
('f102a000-0000-4000-8000-000000000202','f102a000-0000-4000-8000-000000000002','fin02a-demo',2,'PERRO','[{"letra": "P", "estado": "ausente"}, {"letra": "E", "estado": "ausente"}, {"letra": "R", "estado": "ausente"}, {"letra": "R", "estado": "ausente"}, {"letra": "O", "estado": "ausente"}]'::jsonb,'2026-01-02 12:00:00'),
('f102a000-0000-4000-8000-000000000203','f102a000-0000-4000-8000-000000000002','fin02a-demo',3,'PERRO','[{"letra": "P", "estado": "ausente"}, {"letra": "E", "estado": "ausente"}, {"letra": "R", "estado": "ausente"}, {"letra": "R", "estado": "ausente"}, {"letra": "O", "estado": "ausente"}]'::jsonb,'2026-01-02 12:00:00'),
('f102a000-0000-4000-8000-000000000204','f102a000-0000-4000-8000-000000000002','fin02a-demo',4,'PERRO','[{"letra": "P", "estado": "ausente"}, {"letra": "E", "estado": "ausente"}, {"letra": "R", "estado": "ausente"}, {"letra": "R", "estado": "ausente"}, {"letra": "O", "estado": "ausente"}]'::jsonb,'2026-01-02 12:00:00'),
('f102a000-0000-4000-8000-000000000205','f102a000-0000-4000-8000-000000000002','fin02a-demo',5,'PERRO','[{"letra": "P", "estado": "ausente"}, {"letra": "E", "estado": "ausente"}, {"letra": "R", "estado": "ausente"}, {"letra": "R", "estado": "ausente"}, {"letra": "O", "estado": "ausente"}]'::jsonb,'2026-01-02 12:00:00'),
('f102a000-0000-4000-8000-000000000206','f102a000-0000-4000-8000-000000000002','fin02a-demo',6,'PERRO','[{"letra": "P", "estado": "ausente"}, {"letra": "E", "estado": "ausente"}, {"letra": "R", "estado": "ausente"}, {"letra": "R", "estado": "ausente"}, {"letra": "O", "estado": "ausente"}]'::jsonb,'2026-01-02 12:00:00'),
('f102a000-0000-4000-8000-000000000301','f102a000-0000-4000-8000-000000000003','fin02a-demo',1,'SACAS','[{"letra": "S", "estado": "presente"}, {"letra": "A", "estado": "correcto"}, {"letra": "C", "estado": "presente"}, {"letra": "A", "estado": "correcto"}, {"letra": "S", "estado": "correcto"}]'::jsonb,'2026-01-03 12:00:00');
INSERT INTO expected_stats VALUES ('f102a000-0000-4000-8000-000000000009','fin02a-demo',2,1,0,1,1,'2026-01-02 12:00:00');
DO $check$ BEGIN
 IF EXISTS (SELECT 1 FROM public.partidas a JOIN expected_games e ON (a.id=e.id)
            WHERE to_jsonb(a) IS DISTINCT FROM to_jsonb(e)) THEN
  RAISE EXCEPTION 'Synthetic key collision: partidas; no existing records changed';
 END IF;
END $check$;
DO $check$ BEGIN
 IF EXISTS (SELECT 1 FROM public.intentos a JOIN expected_attempts e ON (a.id=e.id)
            WHERE to_jsonb(a) IS DISTINCT FROM to_jsonb(e)) THEN
  RAISE EXCEPTION 'Synthetic key collision: intentos; no existing records changed';
 END IF;
END $check$;
DO $check$ BEGIN
 IF EXISTS (SELECT 1 FROM public.estadisticas a JOIN expected_stats e ON (a.id=e.id OR a.usuario_id=e.usuario_id)
            WHERE to_jsonb(a) IS DISTINCT FROM to_jsonb(e)) THEN
  RAISE EXCEPTION 'Synthetic key collision: estadisticas; no existing records changed';
 END IF;
END $check$;
INSERT INTO public.palabras(palabra)
 SELECT palabra FROM (VALUES ('CASAS'),('GATOS'),('NIÑOS'),('PERRO'),('SACAS')) words(palabra)
 WHERE NOT EXISTS (SELECT 1 FROM public.palabras p WHERE p.palabra=words.palabra)
 ORDER BY palabra;
INSERT INTO public.partidas SELECT * FROM expected_games ON CONFLICT DO NOTHING;
DO $verify$ BEGIN IF EXISTS (SELECT * FROM expected_games EXCEPT SELECT * FROM public.partidas) THEN RAISE EXCEPTION 'Seed incomplete: partidas'; END IF; END $verify$;
INSERT INTO public.intentos SELECT * FROM expected_attempts ON CONFLICT DO NOTHING;
DO $verify$ BEGIN IF EXISTS (SELECT * FROM expected_attempts EXCEPT SELECT * FROM public.intentos) THEN RAISE EXCEPTION 'Seed incomplete: intentos'; END IF; END $verify$;
INSERT INTO public.estadisticas SELECT * FROM expected_stats ON CONFLICT DO NOTHING;
DO $verify$ BEGIN IF EXISTS (SELECT * FROM expected_stats EXCEPT SELECT * FROM public.estadisticas) THEN RAISE EXCEPTION 'Seed incomplete: estadisticas'; END IF; END $verify$;
COMMIT;
