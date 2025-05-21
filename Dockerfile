FROM quay.io/astronomer/astro-runtime:12.8.0

USER root

# ✅ Instalar Java + wget + curl (apenas uma vez)
RUN apt-get update && \
    apt-get install -y openjdk-17-jdk curl wget && \
    apt-get clean

# ✅ Variáveis de ambiente para Spark
ENV JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
ENV PATH=$JAVA_HOME/bin:$PATH
ENV SPARK_HOME=/spark

# ✅ Copiar e extrair Spark local
COPY deps/spark-3.3.0-bin-hadoop3.tgz /tmp/
RUN tar -xvzf /tmp/spark-3.3.0-bin-hadoop3.tgz -C / && \
    mv /spark-3.3.0-bin-hadoop3 /spark && \
    ln -s /spark/bin/spark-submit /usr/bin/spark-submit

# ✅ Criar diretório de JARs
RUN mkdir -p /spark/jars

# ✅ Baixar dependências JARs para acesso ao S3
RUN wget https://repo1.maven.org/maven2/org/apache/hadoop/hadoop-aws/3.3.2/hadoop-aws-3.3.2.jar -P /spark/jars/
RUN wget https://repo1.maven.org/maven2/com/amazonaws/aws-java-sdk-bundle/1.11.1026/aws-java-sdk-bundle-1.11.1026.jar -P /spark/jars/

USER astro
