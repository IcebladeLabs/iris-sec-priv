# Use Ubuntu 22.04 as the base image
FROM ubuntu:22.04
# Set environment variables to noninteractive (for apt-get)
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update
RUN apt-get install -y curl sudo nano software-properties-common vim git wget curl python3 python3-pip unzip tar 
RUN add-apt-repository ppa:openjdk-r/ppa

# Install dependencies
RUN apt-get update && apt-get install -y \
    wget \
    curl \
    tar \
    unzip \
    git \
    software-properties-common \
    apt-transport-https \
    ca-certificates \
    lsb-release


# Install OpenJDK 8, 11, and 17
RUN apt-get update && \
    apt-get install -y openjdk-8-jdk openjdk-11-jdk openjdk-17-jdk 


# Create directory for Maven
ENV MAVEN_DIR=/opt/maven
RUN mkdir -p $MAVEN_DIR

# Download and extract Maven versions
# Maven 3.2.1
RUN wget https://archive.apache.org/dist/maven/maven-3/3.2.1/binaries/apache-maven-3.2.1-bin.tar.gz -P /tmp && \
    tar -xzf /tmp/apache-maven-3.2.1-bin.tar.gz -C $MAVEN_DIR && \
    rm /tmp/apache-maven-3.2.1-bin.tar.gz

# Maven 3.5.0
RUN wget https://archive.apache.org/dist/maven/maven-3/3.5.0/binaries/apache-maven-3.5.0-bin.tar.gz -P /tmp && \
    tar -xzf /tmp/apache-maven-3.5.0-bin.tar.gz -C $MAVEN_DIR && \
    rm /tmp/apache-maven-3.5.0-bin.tar.gz

# Maven 3.9.8
RUN wget https://archive.apache.org/dist/maven/maven-3/3.9.8/binaries/apache-maven-3.9.8-bin.tar.gz -P /tmp && \
    tar -xzf /tmp/apache-maven-3.9.8-bin.tar.gz -C $MAVEN_DIR && \
    rm /tmp/apache-maven-3.9.8-bin.tar.gz


RUN rm -rf /var/lib/apt/lists/*
# Set JAVA_HOME (defaults to JDK 17)
ENV JAVA_HOME=/usr/lib/jvm/java-1.17.0-openjdk-amd64

# Add Maven 3.9.8 to PATH (default)
ENV MAVEN_HOME=/opt/maven/apache-maven-3.9.8
ENV PATH=$MAVEN_HOME/bin:$PATH

# Install multiple Gradle versions
ENV GRADLE_HOME=/opt/gradle
RUN mkdir -p /opt/gradle && \
    for version in 6.8.2 7.6.4 8.9; do \
        wget -q https://services.gradle.org/distributions/gradle-${version}-bin.zip -O /tmp/gradle-${version}-bin.zip && \
        unzip -q /tmp/gradle-${version}-bin.zip -d /opt/gradle && \
        rm /tmp/gradle-${version}-bin.zip; \
    done

ENV PATH=/opt/gradle/gradle-8.9/bin:$PATH

# Verify installations
RUN java -version 
RUN mvn -version
RUN gradle --version



ENV CONDA_DIR=/opt/conda
ENV PATH=$CONDA_DIR/bin:$PATH

# Install Miniconda based on architecture
RUN ARCH=$(uname -m) && \
    if [ "$ARCH" = "x86_64" ]; then \
        CONDA_URL=https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh; \
    elif [ "$ARCH" = "aarch64" ]; then \
        CONDA_URL=https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-aarch64.sh; \
    else \
        echo "Unsupported architecture: $ARCH"; exit 1; \
    fi && \
    wget --quiet $CONDA_URL -O /tmp/miniconda.sh && \
    chmod +x /tmp/miniconda.sh && \
    /tmp/miniconda.sh -b -p $CONDA_DIR && \
    rm /tmp/miniconda.sh && \
    conda clean -afy
# Verify Conda installation
RUN conda --version



COPY .. /iris/
WORKDIR /iris

RUN chmod +x scripts/setup_environment.sh
RUN bash ./scripts/setup_environment.sh

SHELL ["/bin/bash", "-c"]
#RUN echo "conda activate $(head -1 environment.yml | cut -d' ' -f2)" >> ~/.bashrc
RUN ENV_NAME=$(head -1 environment.yml | cut -d' ' -f2) && \
    conda init bash && \
    echo ". /opt/conda/etc/profile.d/conda.sh" >> ~/.bashrc && \
    echo "conda activate $ENV_NAME" >> ~/.bashrc

# Default command (bash shell)
CMD ["/bin/bash"]