# README

## 実行方法

`pip install < requirements.txt`

### 数値シミュレータ

```
    cd core
    python run.py
```

### 可視化

```
cd twinu_web
daphne twinu_web.asgi:application
```

- `localhost:8000/model.html`にアクセス  
- 「Doit」を押すと動く（オブジェクトが表示されるまで時間がかかる）
- 「Layer」を一回押すと見やすくなる
