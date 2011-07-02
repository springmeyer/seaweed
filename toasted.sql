SELECT pg_size_pretty(pg_relation_size('operations'::regclass)), pg_size_pretty(pg_total_relation_size('operations'::regclass));
SELECT nspname, relname,
pg_size_pretty(tablesize) AS tablesize,
pg_size_pretty(indexsize) AS indexsize,
pg_size_pretty(toastsize) AS toastsize,
pg_size_pretty(toastindexsize) AS toastindexsize,
pg_size_pretty(tablesize+indexsize+toastsize+toastindexsize) AS totalsize
FROM
(SELECT ns.nspname, cl.relname, pg_relation_size(cl.oid) AS tablesize,
COALESCE((SELECT SUM(pg_relation_size(indexrelid))::bigint
FROM pg_index WHERE cl.oid=indrelid), 0) AS indexsize,
CASE WHEN reltoastrelid=0 THEN 0
ELSE pg_relation_size(reltoastrelid)
END AS toastsize,
CASE WHEN reltoastrelid=0 THEN 0
ELSE pg_relation_size((SELECT reltoastidxid FROM pg_class ct
WHERE ct.oid = cl.reltoastrelid))
END AS toastindexsize
FROM pg_class cl, pg_namespace ns
WHERE cl.relnamespace = ns.oid
AND ns.nspname NOT IN ('pg_catalog', 'information_schema')
AND cl.relname IN
(SELECT table_name FROM information_schema.TABLES
WHERE table_type = 'BASE TABLE')) ss
ORDER BY tablesize+indexsize+toastsize+toastindexsize DESC;