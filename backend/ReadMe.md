# Backend for Keycloak Handon

## Environment

```shell
- Python 3.13
- Ubuntu 24.04 on WSL
```

## Python

```shell
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt update
sudo apt install python3.13 python3.13-venv python3.13-dev
```

## Install

```shell
python3.13 -m venv venv
. ./venv/bin/activate

pip install --upgrade pip
pip install -r requirements.txt
```

## Run

```
uvicorn main:app --reload
```