import json


def build_key_where_template(key_columns):
    conditions = []
    for i in range(len(key_columns)):
        parts = []
        for j in range(i):
            parts.append(f"{key_columns[j]} = ?")
        parts.append(f"{key_columns[i]} > ?")
        conditions.append("(" + " AND ".join(parts) + ")")
    return " AND (" + " OR ".join(conditions) + ")"


def build_key_params(key_columns, last_keys):
    params = []
    for i in range(len(key_columns)):
        for j in range(i):
            params.append(last_keys[key_columns[j]])
        params.append(last_keys[key_columns[i]])
    return params


def extract_mssql_chunks(
    conn,
    table_name__full,
    table_name__short,
    key_columns,
    where_clause="",
    chunk_size=100000,
):
    last_keys = None
    while True:
        sql = f"""
        SELECT TOP({chunk_size})
        (SELECT t.* FOR JSON PATH, WITHOUT_ARRAY_WRAPPER) AS json_payload
        FROM {table_name__full} t
        WHERE 1 = 1
        """
        metadata = []
        if where_clause:
            sql += f" AND ({where_clause})"
        if last_keys is not None:
            sql += build_key_where_template(key_columns)
        sql += f" ORDER BY {', '.join(key_columns)}"
        with conn.cursor() as cur:
            if last_keys is not None:
                params = build_key_params(key_columns, last_keys)
                cur.execute(sql, params)
            else:
                cur.execute(sql)
            rows = cur.fetchall()
            json_strings = [row[0] for row in rows]
            if not json_strings:
                break
            last_row = json_strings[-1]
            parsed = json.loads(last_row)
            last_keys = {col: parsed.get(col) for col in key_columns}
        for json_str in json_strings:
            parsed = json.loads(json_str)
            sub_json = {k: parsed[k] for k in key_columns if k in parsed}
            business_keys_json = json.dumps(sub_json, separators=(",", ":"))
            metadata.append(
                (
                    table_name__short,
                    business_keys_json,
                )
            )
        yield metadata, json_strings


'''
def get_columns(conn, schema, table):
    sql = """
    SELECT COLUMN_NAME
    FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_SCHEMA = ?
      AND TABLE_NAME = ?
    ORDER BY ORDINAL_POSITION
    """
    return [r[0] for r in conn.execute(sql, (schema, table)).fetchall()]

def build_select(columns):
    selects = [
        f"CAST([{c}] AS VARCHAR(8000)) AS [{c}]"
        for c in columns
    ]
    return f"{', '.join(selects)}"

def extract_mssql_chunks_as_dict(conn, table, key_columns, where_clause="", chunk_size=100000):
    last_keys = None
    columns = get_columns(conn, "dbo", table)
    col_index = {c: i for i, c in enumerate(columns)}
    select_sql = build_select(columns)
    while True:
        sql = f"""
        SELECT TOP ({chunk_size}) {select_sql}
        FROM {table}
        WHERE 1 = 1
        """
        if where_clause:
            sql += f" AND ({where_clause})"
        if last_keys is not None:
            sql += build_key_where_template(key_columns)
        sql += f" ORDER BY {', '.join(key_columns)} ASC"
        with conn.cursor() as cur:
            if last_keys is not None:
                params = build_key_params(key_columns, last_keys)
                cur.execute(sql, params)
            else:
                cur.execute(sql)
            rows = cur.fetchall()
            if not rows:
                break
            last_row = rows[-1]
            last_keys = {
                col: last_row[col_index[col]]
                for col in key_columns
            }
            print(last_keys)
        yield columns, rows

def extract_mssql_chunks_as_dict_json_output(conn, table_name__full, table_name__short, key_columns, where_clause=""):
    for columns, rows in extract_mssql_chunks_as_dict(conn, table_name__full, key_columns, where_clause):
        key_idx = {c: i for i, c in enumerate(columns)}
        key_positions = [key_idx[c] for c in key_columns]
        output_rows = []
        for row in rows:
            key_values = "|".join(str(row[i]) for i in key_positions)
            metadata = (
                table_name__short,
                "|".join(key_columns),
                key_values)
            payload = orjson.dumps(dict(zip(columns, row))).decode()
            output_rows.append((metadata, payload))
        yield output_rows        

def ingestion_from_dict(conn,source_system,table_name__full,table_name__short,key_columns,where_clause=""):
    for columns, rows in extract_mssql_chunks_as_dict(conn,table_name__full,key_columns,where_clause):
        key_idx = {c: i for i, c in enumerate(columns)}
        key_positions = [key_idx[c] for c in key_columns]
        buffer = io.StringIO()
        writer = csv.writer(buffer)
        for row in rows:
            key_values = "|".join(str(row[i]) for i in key_positions)
            payload = orjson.dumps(dict(zip(columns, row))).decode()
            writer.writerow([
                1,
                1,
                source_system,
                table_name__short,
                str(key_columns),
                key_values,
                payload
            ])
        buffer.seek(0)
        with pg() as conn_pg:
            with conn_pg.cursor() as cur:
                cur.copy_expert("""
                    COPY bronze.raw_landing (
                        load_id,
                        batch_id,
                        source_system,
                        source_table,
                        business_key,
                        business_key_value,
                        payload
                    )
                    FROM STDIN WITH (FORMAT CSV)
                """, buffer)
            conn_pg.commit()

'''
