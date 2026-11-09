-- Run with psql -X -v ON_ERROR_STOP=1 only against the disposable local target.
-- Read-only catalog checks, after initial_wordle.sql, before optional RLS.
DO $test$
DECLARE
    expected record;
    actual record;
    target_table text;
    total integer;
BEGIN
    FOR expected IN SELECT * FROM (VALUES
        ('palabras','id','int4',true,'sequence'),
        ('palabras','palabra','varchar',true,'none'),
        ('partidas','id','uuid',true,'uuid'),
        ('partidas','usuario_id','text',true,'none'),
        ('partidas','palabra_secreta','varchar',true,'none'),
        ('partidas','intentos_usados','int4',false,'zero'),
        ('partidas','estado','varchar',false,'state'),
        ('partidas','created_at','timestamp',false,'now'),
        ('intentos','id','uuid',true,'uuid'),
        ('intentos','partida_id','uuid',false,'none'),
        ('intentos','usuario_id','text',true,'none'),
        ('intentos','numero','int4',true,'none'),
        ('intentos','palabra','varchar',true,'none'),
        ('intentos','resultado','jsonb',true,'none'),
        ('intentos','created_at','timestamp',false,'now'),
        ('estadisticas','id','uuid',true,'uuid'),
        ('estadisticas','usuario_id','text',true,'none'),
        ('estadisticas','partidas_jugadas','int4',false,'zero'),
        ('estadisticas','partidas_ganadas','int4',false,'zero'),
        ('estadisticas','racha_actual','int4',false,'zero'),
        ('estadisticas','racha_maxima','int4',false,'zero'),
        ('estadisticas','intentos_promedio','numeric',false,'zero'),
        ('estadisticas','updated_at','timestamp',false,'now')
    ) AS columns(table_name,column_name,type_name,not_null,default_kind)
    LOOP
        SELECT a.attnotnull AS not_null, t.typname AS type_name, a.atttypmod,
               pg_get_expr(d.adbin,d.adrelid) AS default_value
          INTO actual
          FROM pg_attribute a
          JOIN pg_type t ON t.oid=a.atttypid
          LEFT JOIN pg_attrdef d ON d.adrelid=a.attrelid AND d.adnum=a.attnum
         WHERE a.attrelid=to_regclass('public.' || expected.table_name)
           AND a.attname=expected.column_name AND a.attnum>0 AND NOT a.attisdropped;
        IF NOT FOUND THEN RAISE EXCEPTION 'Missing %.%',expected.table_name,expected.column_name; END IF;
        IF actual.type_name<>expected.type_name OR actual.not_null<>expected.not_null THEN
            RAISE EXCEPTION 'Type/null mismatch %.%',expected.table_name,expected.column_name;
        END IF;
        IF actual.type_name IN ('varchar','numeric') AND actual.atttypmod<>-1 THEN
            RAISE EXCEPTION 'Unexpected length/precision %.%',expected.table_name,expected.column_name;
        END IF;
        IF (expected.default_kind='none' AND actual.default_value IS NOT NULL)
           OR (expected.default_kind='zero' AND coalesce(actual.default_value,'') NOT IN ('0','0::numeric'))
           OR (expected.default_kind='uuid' AND coalesce(actual.default_value,'')<>'gen_random_uuid()')
           OR (expected.default_kind='now' AND coalesce(actual.default_value,'')<>'now()')
           OR (expected.default_kind='state' AND coalesce(actual.default_value,'')<>quote_literal('en_curso') || '::character varying')
           OR (expected.default_kind='sequence' AND (coalesce(actual.default_value,'') NOT LIKE 'nextval(%' OR actual.default_value NOT LIKE '%palabras_id_seq%'))
        THEN RAISE EXCEPTION 'Default mismatch %.%',expected.table_name,expected.column_name;
        END IF;
    END LOOP;

    SELECT count(*) INTO total FROM information_schema.columns
     WHERE table_schema='public' AND table_name IN ('palabras','partidas','intentos','estadisticas');
    IF total<>23 THEN RAISE EXCEPTION 'Expected 23 columns, got %',total; END IF;

    FOREACH target_table IN ARRAY ARRAY['palabras','partidas','intentos','estadisticas'] LOOP
        IF (SELECT count(*) FROM pg_constraint
            WHERE conrelid=to_regclass('public.' || target_table) AND contype='p'
              AND pg_get_constraintdef(oid)='PRIMARY KEY (id)')<>1 THEN
            RAISE EXCEPTION 'Unexpected primary key: %',target_table;
        END IF;
        IF EXISTS (SELECT 1 FROM pg_trigger WHERE tgrelid=to_regclass('public.' || target_table) AND NOT tgisinternal) THEN
            RAISE EXCEPTION 'Unexpected user trigger: %',target_table;
        END IF;
    END LOOP;
    IF (SELECT count(*) FROM pg_constraint WHERE conrelid='public.palabras'::regclass AND contype='u' AND pg_get_constraintdef(oid)='UNIQUE (palabra)')<>1
       OR (SELECT count(*) FROM pg_constraint WHERE conrelid='public.estadisticas'::regclass AND contype='u' AND pg_get_constraintdef(oid)='UNIQUE (usuario_id)')<>1 THEN
        RAISE EXCEPTION 'Missing expected UNIQUE constraints';
    END IF;
    IF (SELECT count(*) FROM pg_constraint WHERE conrelid='public.intentos'::regclass AND contype='f'
        AND confrelid='public.partidas'::regclass
        AND pg_get_constraintdef(oid)='FOREIGN KEY (partida_id) REFERENCES partidas(id)')<>1 THEN
        RAISE EXCEPTION 'Unexpected foreign key';
    END IF;
    IF (SELECT count(*) FROM pg_indexes WHERE schemaname='public' AND tablename IN ('palabras','partidas','intentos','estadisticas'))<>6 THEN
        RAISE EXCEPTION 'Expected exactly six PK/UNIQUE indexes';
    END IF;
    IF EXISTS (SELECT 1 FROM pg_constraint WHERE conrelid IN ('public.palabras'::regclass,'public.partidas'::regclass,'public.intentos'::regclass,'public.estadisticas'::regclass) AND contype='c') THEN
        RAISE EXCEPTION 'Unexpected CHECK constraint';
    END IF;
    RAISE NOTICE 'PASS: structural catalog contracts';
END
$test$;
