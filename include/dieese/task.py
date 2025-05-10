def inserir_cesta_basica_postgres(csv_s3_path, conn_id):
    import pandas as pd
    import psycopg2
    from airflow.hooks.base import BaseHook
    import json
    import boto3

    conn = BaseHook.get_connection('aws_s3')
    s3 = boto3.client(
        's3',
        aws_access_key_id=conn.login,
        aws_secret_access_key=conn.password,
        region_name=json.loads(conn.extra)['region_name']
    )

    bucket = "ranking-municipios-br"
    key = csv_s3_path.replace(f"s3://{bucket}/", "")
    local_path = "/tmp/cesta_basica.csv"
    s3.download_file(bucket, key, local_path)

    df = pd.read_csv(local_path)
    df = df.rename(columns={"Data": "data_mes"})
    df_melted = df.melt(id_vars=["data_mes"], var_name="cidade", value_name="valor")

    pg_conn = BaseHook.get_connection(conn_id)
    conn_pg = psycopg2.connect(
        dbname=pg_conn.schema,
        user=pg_conn.login,
        password=pg_conn.password,
        host=pg_conn.host,
        port=pg_conn.port
    )
    cursor = conn_pg.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS cesta_basica (
            data_mes TEXT,
            cidade TEXT,
            valor FLOAT,
            PRIMARY KEY (data_mes, cidade)
        );
    """)
    conn_pg.commit()

    for _, row in df_melted.iterrows():
        cursor.execute("""
            INSERT INTO cesta_basica (data_mes, cidade, valor)
            VALUES (%s, %s, %s)
            ON CONFLICT (data_mes, cidade) DO UPDATE SET valor = EXCLUDED.valor;
        """, (row["data_mes"], row["cidade"], row["valor"]))

    conn_pg.commit()
    cursor.close()
    conn_pg.close()
    print("✅ Dados da cesta básica inseridos com sucesso!")
