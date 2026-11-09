-- SQL analogues of backend operations, NOT an HTTP/PostgREST integration test.
-- Disposable LOCAL database only. Synthetic words reuse existing MemoryDB fixtures.
-- Table writes roll back; PostgreSQL sequence nextval increments do NOT roll back.
BEGIN;
DO $test$
DECLARE
    game_id uuid;
    guess_result jsonb := '[{"letra":"C","estado":"correcto"},{"letra":"A","estado":"correcto"},{"letra":"S","estado":"correcto"},{"letra":"A","estado":"correcto"},{"letra":"S","estado":"correcto"}]';
    row_data record;
BEGIN
    IF EXISTS (SELECT 1 FROM public.palabras) OR EXISTS (SELECT 1 FROM public.partidas)
       OR EXISTS (SELECT 1 FROM public.intentos) OR EXISTS (SELECT 1 FROM public.estadisticas) THEN
        RAISE EXCEPTION 'This test requires four empty local tables';
    END IF;
    INSERT INTO public.palabras(palabra) VALUES ('CASAS'),('PERRO');
    BEGIN
        INSERT INTO public.palabras(palabra) VALUES ('CASAS');
        RAISE EXCEPTION 'UNIQUE palabra was not enforced';
    EXCEPTION WHEN unique_violation THEN NULL;
    END;
    INSERT INTO public.partidas(usuario_id,palabra_secreta)
        VALUES ('fin01b-synthetic','CASAS') RETURNING id INTO game_id;
    SELECT * INTO row_data FROM public.partidas WHERE id=game_id LIMIT 1;
    IF row_data.intentos_usados<>0 OR row_data.estado<>'en_curso' OR row_data.created_at IS NULL THEN
        RAISE EXCEPTION 'Partida defaults incompatible';
    END IF;
    INSERT INTO public.intentos(partida_id,usuario_id,numero,palabra,resultado)
        VALUES (game_id,'fin01b-synthetic',1,'CASAS',guess_result);
    IF NOT EXISTS (SELECT 1 FROM public.intentos WHERE partida_id=game_id AND resultado=guess_result AND jsonb_array_length(resultado)=5) THEN
        RAISE EXCEPTION 'JSONB guess roundtrip failed';
    END IF;
    BEGIN
        INSERT INTO public.intentos(partida_id,usuario_id,numero,palabra,resultado)
            VALUES (gen_random_uuid(),'fin01b-synthetic',2,'PERRO',guess_result);
        RAISE EXCEPTION 'Foreign key was not enforced';
    EXCEPTION WHEN foreign_key_violation THEN NULL;
    END;
    UPDATE public.partidas SET intentos_usados=1,estado='ganada' WHERE id=game_id;
    INSERT INTO public.estadisticas(usuario_id,partidas_jugadas,partidas_ganadas,racha_actual,racha_maxima,intentos_promedio)
        VALUES ('fin01b-synthetic',1,1,1,1,1);
    UPDATE public.estadisticas SET intentos_promedio=(intentos_promedio*partidas_ganadas+2)/(partidas_ganadas+1),
        partidas_jugadas=partidas_jugadas+1,partidas_ganadas=partidas_ganadas+1,
        racha_actual=racha_actual+1,racha_maxima=greatest(racha_maxima,racha_actual+1)
        WHERE usuario_id='fin01b-synthetic';
    SELECT * INTO row_data FROM public.estadisticas WHERE usuario_id='fin01b-synthetic';
    IF row_data.intentos_promedio<>1.5 OR row_data.partidas_ganadas<>2 THEN
        RAISE EXCEPTION 'Fractional average/counters incompatible';
    END IF;
    BEGIN
        INSERT INTO public.estadisticas(usuario_id) VALUES ('fin01b-synthetic');
        RAISE EXCEPTION 'UNIQUE usuario_id was not enforced';
    EXCEPTION WHEN unique_violation THEN NULL;
    END;
    -- Verified NULL columns must remain nullable, even if the app normally fills them.
    INSERT INTO public.intentos(partida_id,usuario_id,numero,palabra,resultado)
        VALUES (NULL,'fin01b-synthetic',2,'PERRO',guess_result);
    INSERT INTO public.partidas(usuario_id,palabra_secreta,intentos_usados,estado,created_at)
        VALUES ('fin01b-synthetic','CASAS',NULL,NULL,NULL);
    RAISE NOTICE 'PASS: SQL backend operation analogues (not API/RLS authorization)';
END
$test$;
ROLLBACK;
