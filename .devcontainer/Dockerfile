FROM mcr.microsoft.com/devcontainers/python:3

# Git LFS 설치 (이미지 레벨)
RUN apt-get update \
    && apt-get install -y git-lfs \
    && git lfs install --system \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*
