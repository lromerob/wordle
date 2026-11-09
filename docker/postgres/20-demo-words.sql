-- PG-05: minimal authorized demo fixture, NOT the final approved dictionary.
-- Prepared with FIN-01B prepare_dictionary.build_seed; no external word list.
-- Source SHA256: 5514ec50633a31f546b26021a8a67872f6d7a8c5058cf28d966bed3471736a64
-- Distinct normalized words: 5
-- Apply only during initial creation of a NEW authorized PG-05 demo database.
BEGIN;
INSERT INTO public.palabras (palabra) VALUES
    ('CASAS'),
    ('GATOS'),
    ('NIÑOS'),
    ('PERRO'),
    ('SACAS')
ON CONFLICT (palabra) DO NOTHING;
COMMIT;
