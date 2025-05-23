# [Shingen.py] Pythonで学ぶKeycloakを用いたユーザー管理ハンズオン

## この勉強会について

Shingen.py は山梨のPythonコミュニティが主催する初心者向けワークショップです。  
本ハンズオン「Pythonで学ぶ Keycloak を用いたユーザー管理システム開発」では、以下を実際に体験します。

- Keycloak の基本概念  
- python-keycloak ライブラリを使ったユーザー操作  
- FastAPI との連携による認証・ログイン機能の実装  
- アクセストークンの発行・検証  
- ユーザー登録・管理機能の開発  

Docker を利用した環境構築のため、参加者は PC1台で手軽に実習可能。  
サンプルコードは持ち帰りいただけますので、後日ご自身のプロジェクトにも応用できます。

開催URL: https://shingenpy.connpass.com/event/353887/

## ハンズオン素材

## 必要な環境

- Linux/Macの開発環境 (WSL含む)
- Ubuntu 24.04推奨
- Python 3.12以上
- docker compose (V2)
- Node.js v16+
- npm

## 起動方法

```shell
docker compose up
もしくは docker compose up -d
```

変更を反映してから起動

```shell
docker compose build
docker compose up
```

Keycloak, Backend(FastAPI), Frontend(Vite) が立ち上がります。

| Application | URL                   |
| :---------- | :-------------------- |
| Keycloak    | http://localhost:8080 |
| FastAPI     | http://localhost:8000 |
| Vite        | http://localhost:3000 |