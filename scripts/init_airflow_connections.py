from airflow.models import Connection
from airflow import settings
import os

def create_connection(conn_id, conn_type, login=None, password=None, host=None, extra=None):
    session = settings.Session()
    existing = session.query(Connection).filter_by(conn_id=conn_id).first()
    if existing:
        session.delete(existing)
        session.commit()
        print(f"🗑️ Conexão removida: {conn_id}")
    conn = Connection(
        conn_id=conn_id,
        conn_type=conn_type,
        login=login,
        password=password,
        host=host,
        extra=extra
    )
    session.add(conn)
    session.commit()
    print(f"✅ Conexão criada: {conn_id}")

# 🟡 Kaggle
create_connection(
    conn_id="kaggle_default",
    conn_type="generic",
    login="datamasterrafael",
    password="80243e1ba78e7efb5c5f678cad1be8b5",
    extra='{"file_path": "/home/astro/.kaggle/kaggle.json"}'
)

# 🔵 AWS S3 - usando variáveis de ambiente
create_connection(
    conn_id="aws_s3",
    conn_type="Amazon Web Services",
    login=os.getenv("AWS_ACCESS_KEY_ID"),
    password=os.getenv("AWS_SECRET_ACCESS_KEY"),
    extra='{"region_name": "us-east-2"}'
)

# 🟢 IBGE
create_connection(
    conn_id="ibge_api",
    conn_type="HTTP",
    host="https://ftp.ibge.gov.br",
    login="admin",
    password="admin",
    extra='{"endpoint": "/Estimativas_de_Populacao/Estimativas_2024/POP2024_20241230.xls", "headers": {}}'
)

# 🟣 DIEESE
create_connection(
    conn_id="diese_api",
    conn_type="HTTP",
    host="https://www.dieese.org.br"
)
