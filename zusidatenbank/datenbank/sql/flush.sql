BEGIN;
TRUNCATE "datenbank_streckenmodule_nachbaren", "datenbank_fuehrerstand", "datenbank_fuehrerstand_autor", "datenbank_streckenmodule", "datenbank_fahrplanzug_autor", "datenbank_fahrplanzug", "datenbank_fahrplan", "datenbank_fahrplan_zuege", "datenbank_autor", "datenbank_fahrzeugvariante_autor", "datenbank_fahrplanzugeintrag", "datenbank_fahrplan_strecken_modules", "datenbank_fahrplanzug_fahrzeuge", "datenbank_fahrzeugvariante", "datenbank_fahrplan_autor", "datenbank_streckenmodule_autor";
SELECT setval(pg_get_serial_sequence('"datenbank_fahrzeugvariante"','id'), 1, false);
SELECT setval(pg_get_serial_sequence('"datenbank_fahrplanzugeintrag"','id'), 1, false);
COMMIT;
