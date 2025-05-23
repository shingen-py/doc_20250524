import React, { useEffect, useState } from "react";

const App: React.FC = () => {
  const [logged, setLogged] = useState<boolean>(false);
  const [loading, setLoading] = useState<boolean>(false);

  useEffect(() => {
    // ログイン済みチェック
    fetch("http://localhost:8000/api/auth/me", {
      credentials: "include"
    })
      .then(res => {
        if (res.ok) setLogged(true);
      })
      .catch(() => {
        setLogged(false);
      });
  }, []);

  const onLogin = () => {
    setLoading(true);
    // ログイン開始
    window.location.href =
      "http://localhost:8000/api/auth/login?state=/";
  };

  return (
    <div style={{ textAlign: "center", marginTop: "20vh" }}>
      {!logged ? (
        loading ? (
          // シンプル CSS スピナー
          <div
            style={{
              border: "4px solid #f3f3f3",
              borderTop: "4px solid #3C8DBC",
              borderRadius: "50%",
              width: "32px",
              height: "32px",
              animation: "spin 1s linear infinite",
              margin: "auto"
            }}
          />
        ) : (
          <button
            onClick={onLogin}
            style={{
              fontSize: "1.2rem",
              padding: "0.8rem 1.6rem",
              cursor: "pointer"
            }}
          >
            Login
          </button>
        )
      ) : (
        <h1>ログインが完了しました！</h1>
      )}
      <style>
        {`
          @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
          }
        `}
      </style>
    </div>
  );
};

export default App;
