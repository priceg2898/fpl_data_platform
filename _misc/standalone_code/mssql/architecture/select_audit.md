## SELECT audit for MSSQL


#### Set up at server level:
```
USE master;
GO

ALTER SERVER AUDIT [Track_Object_Usage_Audit]
TO FILE ( 
    FILEPATH = N'C:\SQLServerAudit\',  -- Make sure this folder exists on the server
    MAXSIZE = 100 MB,
    MAX_ROLLOVER_FILES = 50,
    RESERVE_DISK_SPACE = ON
)
WITH (QUEUE_DELAY = 1000, ON_FAILURE = CONTINUE);
GO

-- Enable the audit container
ALTER SERVER AUDIT [Track_Object_Usage_Audit] WITH (STATE = ON);
```

#### Apply to Databases:
```
DECLARE @db VARCHAR(100);
DECLARE @Qry NVARCHAR(MAX);

DECLARE db_cursor CURSOR FOR
    SELECT name
    FROM sys.databases
    WHERE LEFT(name,2) IN ('T1','T2','T3');

OPEN db_cursor;

FETCH NEXT FROM db_cursor INTO @db;

WHILE @@FETCH_STATUS = 0
BEGIN

    PRINT CONCAT(@db, ' started...');

    SET @Qry = N'
    USE ' + QUOTENAME(@db) + N';

    -- Drop Audit Specs safely
    IF EXISTS (SELECT 1 FROM sys.database_audit_specifications WHERE name = ''Track_DB_Changes'')
    BEGIN
        ALTER DATABASE AUDIT SPECIFICATION [Track_DB_Changes] WITH (STATE = OFF);
        DROP DATABASE AUDIT SPECIFICATION [Track_DB_Changes];
    END;

    IF EXISTS (SELECT 1 FROM sys.database_audit_specifications WHERE name = ''Audit_All_Reads'')
    BEGIN
        ALTER DATABASE AUDIT SPECIFICATION [Audit_All_Reads] WITH (STATE = OFF);
        DROP DATABASE AUDIT SPECIFICATION [Audit_All_Reads];
    END;

    -- Recreate cleanly
    CREATE DATABASE AUDIT SPECIFICATION [Audit_All_Reads]
    FOR SERVER AUDIT [Track_Object_Usage_Audit]
    ADD (SELECT ON DATABASE::' + QUOTENAME(@db) + N' BY PUBLIC)
    WITH (STATE = ON);
    ';

    EXEC sp_executesql @Qry;

    PRINT CONCAT(@db, ' finished...');

    FETCH NEXT FROM db_cursor INTO @db;
END;

CLOSE db_cursor;
DEALLOCATE db_cursor;
```


```
DECLARE @SQL NVARCHAR(MAX) = N'';

IF OBJECT_ID('tempdb..#t') IS NOT NULL DROP TABLE #t

CREATE TABLE #t
    (   database_id INT NOT NULL,
        database_name VARCHAR(100),
        schema_name VARCHAR(50),
        object_name VARCHAR(200),
        object_id INT NOT NULL,
        type VARCHAR(1),
        type_desc VARCHAR(20)
        PRIMARY KEY (database_id, object_id))

SELECT @SQL += '
SELECT
    ' + CAST(database_id AS VARCHAR(10)) + ' AS database_id,
    ''' + name + ''' AS DatabaseName,
    s.name COLLATE Latin1_General_CI_AS AS SchemaName,
    o.name COLLATE Latin1_General_CI_AS AS ObjectName,
    o.object_id,
    o.type,
    o.type_desc
FROM ' + QUOTENAME(name) + '.sys.objects o
JOIN ' + QUOTENAME(name) + '.sys.schemas s
    ON o.schema_id = s.schema_id
WHERE o.type IN (''U'', ''V'') -- U = table, V = view
UNION ALL
'
FROM sys.databases
WHERE state_desc = 'ONLINE'
AND database_id > 4;

-- Remove trailing UNION ALL
SET @SQL = LEFT(@SQL, LEN(@SQL) - 11);

INSERT INTO #t EXEC sp_executesql @SQL;

ALTER TABLE #t ADD num_selects INT
ALTER TABLE #t ADD most_selects_user VARCHAR(100)
ALTER TABLE #t ADD last_select_date DATETIME
ALTER TABLE #t ADD last_select_user VARCHAR(100)
ALTER TABLE #t ADD last_select_statement VARCHAR(8000)

IF OBJECT_ID('tempdb..#SelectsAudit') IS NOT NULL DROP TABLE #SelectsAudit

SELECT database_principal_id, object_id, CAST(event_time AS DATETIME) event_time, session_server_principal_name, statement INTO #SelectsAudit FROM sys.fn_get_audit_file('C:\SQLServerAudit\*.sqlaudit',DEFAULT,DEFAULT)
CREATE CLUSTERED INDEX CI_database_principal_id_object_id ON #SelectsAudit (database_principal_id, object_id)
CREATE NONCLUSTERED INDEX NCI_event_date ON #SelectsAudit (event_time) INCLUDE (database_principal_id, object_id)

UPDATE #t
SET
num_selects = ( SELECT COUNT(*)
                FROM #SelectsAudit s
                WHERE t.database_id = s.database_principal_id
                AND t.object_id = s.object_id),
last_select_date = (    SELECT MAX(s.event_time)
                        FROM #SelectsAudit s
                        WHERE t.database_id = s.database_principal_id
                        AND t.object_id = s.object_id)
FROM #t t

UPDATE #t
SET
last_select_user = (    SELECT TOP(1) session_server_principal_name
                        FROM #SelectsAudit s
                        WHERE 1 = 1
                        AND t.database_id = s.database_principal_id
                        AND t.object_id = s.object_id
                        AND t.last_select_date = s.event_time
                        AND s.session_server_principal_name IS NOT NULL),
last_select_statement = (   SELECT TOP(1) s.statement
                            FROM #SelectsAudit s
                            WHERE 1 = 1
                            AND t.database_id = s.database_principal_id
                            AND t.object_id = s.object_id
                            AND t.last_select_date = s.event_time
                            AND s.statement IS NOT NULL)
FROM #t t

;WITH 
c1 AS ( SELECT s.database_principal_id database_id, s.object_id, s.session_server_principal_name user_id, COUNT(*) Cnt
        FROM #SelectsAudit s
        GROUP BY s.database_principal_id, s.object_id, session_server_principal_name),
c2 AS ( SELECT c1.database_id, c1.object_id, MAX(Cnt) MaxCnt FROM c1 GROUP BY c1.database_id, c1.object_id),
c3 AS ( SELECT ROW_NUMBER() OVER(PARTITION BY c1.database_id, c1.object_id ORDER BY c1.user_id) RowNo, c1.database_id, c1.object_id, user_id
        FROM c1
        JOIN c2 ON c2.database_id = c1.database_id AND c2.object_id = c1.object_id AND c2.MaxCnt = c1.Cnt)


UPDATE #t SET most_selects_user = c3.user_id
FROM #t t
LEFT JOIN c3 ON c3.database_id = t.database_id AND c3.object_id = t.object_id AND c3.RowNo = 1

SELECT * FROM #t ORDER BY num_selects DESC, database_id, OBJECT_ID
```