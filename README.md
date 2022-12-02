# Torrent_Proxy
BitTorrentで共有されたコンテンツをCCNから利用可能にするプロキシの実装を行いました。
※現在，全体を改良中

- [Proxy](#Proxy)
    - [概要](#概要)

<a id="Proxy"></a>
## Proxy

### 概要
Proxyは，BitTorrentのピースを要求するInterestを受け付けるモジュールである．
以下のような機能を持つ．

* `ccnx:/BitTorrent/info_hash/piece_index` の名前を持つInterestを受信．
* info_hashに基づくコンテンツのピース(piece_indexのピース)をDataとして送信．
* info_hashに基づくコンテンツを所持していない場合は，BitTorrentでピースを取得．
  * トラッカー接続を行い，ピアリストを入手する．
  * ピアリストからピアに接続し，ハンドシェイクを行う．
  * ピアにピース取得メッセージを送信．
  * ピースを受け取る．

### 使用方法
現在、dockerによるデモの簡略化を進行中
ceforeをインストール・ビルドし、ceforeの機能を試すだけなら可能
image:cefore/base　必要なコンポーネントが包含されているimage.

* cefore/producer
コンテンツ生産者
一般にコンテンツサーバー
* cefore/router
CCNルーター
* cefore/consumer
コンテンツ消費者
一般にクライアント
```bash
cd cefore_demo
./setup.sh
docker-compose up
```

