FROM ubuntu:22.04

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive
ENV PYENV_ROOT="/root/.pyenv"
ENV PATH="$PYENV_ROOT/bin:$PATH"

# Update and install prerequisites
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    unzip \
    build-essential \
    libssl-dev \
    zlib1g-dev \
    libbz2-dev \
    libreadline-dev \
    libsqlite3-dev \
    make \
    sudo \
    pipx \
    git \
    python3.11 \
    python3.11-venv \
    python3.11-dev \
    python3-pip \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Install Dotnet
RUN apt-get update && apt-get install -y software-properties-common \
    && sudo add-apt-repository ppa:dotnet/backports \
    && apt-get update && apt-get install -y dotnet-sdk-6.0

# Install Dafny
RUN wget https://github.com/dafny-lang/dafny/releases/download/v4.3.0/dafny-4.3.0-x64-ubuntu-20.04.zip \
    && unzip dafny-4.3.0-x64-ubuntu-20.04.zip \
    && export PATH="$PATH:$(pwd)/dafny-4.3.0"

# Install Pyenv
RUN curl https://pyenv.run | bash \
    && echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.bashrc \
    && echo 'export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.bashrc \
    && echo -e 'eval "$(pyenv init --path)"\neval "$(pyenv virtualenv-init -)"' >> ~/.bashrc

# Install Poetry
RUN pipx install poetry \
    && pipx ensurepath

# Set env variable 
ENV PATH="/root/.local/bin:$PATH"

# Check poetry install
RUN poetry --version

# Clean up
RUN rm -f dafny-4.3.0-x64-ubuntu-20.04.zip

RUN git clone --recurse-submodules https://github.com/emugnier/dafny_repair.git
WORKDIR SOMETHING
RUN git checkout SOMETHING

# Default command
CMD ["/bin/bash"]
