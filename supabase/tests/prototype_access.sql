-- Catalog checks AFTER optional prototype/allow_all.sql in LOCAL Supabase only.
-- Does not prove isolation; the reproduced policy is deliberately allow-all.
DO $test$
DECLARE t text; r text; privilege text;
BEGIN
    FOREACH t IN ARRAY ARRAY['palabras','partidas','intentos','estadisticas'] LOOP
        IF NOT EXISTS (SELECT 1 FROM pg_class WHERE oid=to_regclass('public.'||t) AND relrowsecurity AND NOT relforcerowsecurity) THEN
            RAISE EXCEPTION 'RLS flags mismatch: %',t;
        END IF;
        IF (SELECT count(*) FROM pg_policy WHERE polrelid=to_regclass('public.'||t))<>1
           OR NOT EXISTS (SELECT 1 FROM pg_policy WHERE polrelid=to_regclass('public.'||t)
               AND polname='allow_all' AND polpermissive AND polcmd='*'
               AND polroles=ARRAY[0::oid] AND pg_get_expr(polqual,polrelid)='true' AND polwithcheck IS NULL) THEN
            RAISE EXCEPTION 'Prototype policy mismatch: %',t;
        END IF;
        FOREACH r IN ARRAY ARRAY['anon','authenticated','service_role'] LOOP
            FOREACH privilege IN ARRAY ARRAY['SELECT','INSERT','UPDATE','DELETE'] LOOP
                IF NOT has_table_privilege(r,'public.'||t,privilege) THEN
                    RAISE EXCEPTION 'Missing prototype table privilege: % % %',r,t,privilege;
                END IF;
            END LOOP;
        END LOOP;
    END LOOP;
    RAISE NOTICE 'PASS: prototype access metadata, not authorization hardening';
END
$test$;
