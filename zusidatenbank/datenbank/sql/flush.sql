BEGIN;
TRUNCATE "datenbank_streckenmodule_nachbaren", "datenbank_fuehrerstand", "datenbank_fuehrerstand_autor", "datenbank_streckenmodule", "datenbank_fahrplanzug_autor", "datenbank_fahrplanzug", "datenbank_fahrplan", "datenbank_fahrplan_zuege", "datenbank_autor", "datenbank_fahrzeugvariante_autor", "datenbank_fahrplanzugeintrag", "datenbank_fahrplan_strecken_modules", "datenbank_fahrplanzug_fahrzeuge", "datenbank_fahrzeugvariante", "datenbank_fahrplan_autor", "datenbank_streckenmodule_autor", "datenbank_fuehrerstandblick";

SELECT setval(pg_get_serial_sequence('"datenbank_fahrplanzugeintrag"','id'), 1, false);
SELECT setval(pg_get_serial_sequence('"datenbank_streckenmodule_nachbaren"','id'), coalesce(max("id"), 1), max("id") IS NOT null) FROM "datenbank_streckenmodule_nachbaren";
SELECT setval(pg_get_serial_sequence('"datenbank_streckenmodule_autor"','id'), coalesce(max("id"), 1), max("id") IS NOT null) FROM "datenbank_streckenmodule_autor";
SELECT setval(pg_get_serial_sequence('"datenbank_fuehrerstand_autor"','id'), coalesce(max("id"), 1), max("id") IS NOT null) FROM "datenbank_fuehrerstand_autor";
SELECT setval(pg_get_serial_sequence('"datenbank_fahrzeugvariante_autor"','id'), coalesce(max("id"), 1), max("id") IS NOT null) FROM "datenbank_fahrzeugvariante_autor";
SELECT setval(pg_get_serial_sequence('"datenbank_fahrzeugvariante"','id'), coalesce(max("id"), 1), max("id") IS NOT null) FROM "datenbank_fahrzeugvariante";
SELECT setval(pg_get_serial_sequence('"datenbank_fahrplanzug_fahrzeuge"','id'), coalesce(max("id"), 1), max("id") IS NOT null) FROM "datenbank_fahrplanzug_fahrzeuge";
SELECT setval(pg_get_serial_sequence('"datenbank_fahrplanzug_autor"','id'), coalesce(max("id"), 1), max("id") IS NOT null) FROM "datenbank_fahrplanzug_autor";
SELECT setval(pg_get_serial_sequence('"datenbank_fahrplanzugeintrag"','id'), coalesce(max("id"), 1), max("id") IS NOT null) FROM "datenbank_fahrplanzugeintrag";
SELECT setval(pg_get_serial_sequence('"datenbank_fahrplan_strecken_modules"','id'), coalesce(max("id"), 1), max("id") IS NOT null) FROM "datenbank_fahrplan_strecken_modules";
SELECT setval(pg_get_serial_sequence('"datenbank_fahrplan_zuege"','id'), coalesce(max("id"), 1), max("id") IS NOT null) FROM "datenbank_fahrplan_zuege";
SELECT setval(pg_get_serial_sequence('"datenbank_fahrplan_autor"','id'), coalesce(max("id"), 1), max("id") IS NOT null) FROM "datenbank_fahrplan_autor";
SELECT setval(pg_get_serial_sequence('"datenbank_fuehrerstandblick"','id'), coalesce(max("id"), 1), max("id") IS NOT null) FROM "datenbank_fuehrerstandblick";

COMMIT;
