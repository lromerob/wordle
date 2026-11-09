-- OPTIONAL reproduction of the verified INSECURE prototype access model.
-- NOT production hardening; NEVER applied automatically with migrations.
-- Local Supabase roles anon/authenticated/service_role must already exist.
-- No role creation, passwords, schema/sequence/default grants or FORCE RLS.
BEGIN;

ALTER TABLE public.palabras ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.partidas ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.intentos ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.estadisticas ENABLE ROW LEVEL SECURITY;

CREATE POLICY allow_all ON public.palabras AS PERMISSIVE FOR ALL TO PUBLIC USING (true);
CREATE POLICY allow_all ON public.partidas AS PERMISSIVE FOR ALL TO PUBLIC USING (true);
CREATE POLICY allow_all ON public.intentos AS PERMISSIVE FOR ALL TO PUBLIC USING (true);
CREATE POLICY allow_all ON public.estadisticas AS PERMISSIVE FOR ALL TO PUBLIC USING (true);

GRANT SELECT, INSERT, UPDATE, DELETE
ON TABLE public.palabras, public.partidas, public.intentos, public.estadisticas
TO anon, authenticated, service_role;

COMMIT;
