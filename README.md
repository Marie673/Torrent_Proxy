# Torrent_Proxy
※現在，全体を改良中

- [Proxy](#Proxy)
    - [概要](#概要)
    - [構成](#構成)
    - [使用方法](#使用方法)

- [Client](#Client)
    - [概要](#概要1)
    - [構成](#構成1)
    - [使用方法](#使用方法1)

- [lib](#lib)
  
- [注意事項](#注意事項)

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
  
### 構成
以下のファイルから構成される．

* `src/proxy/proxy.py`: Interestを受信し，ピースをDataとして送信する主要ファイル．
* `src/proxy/downloader.py`: BitTorrentによるピースの取得を行うファイル．
* `src/proxy/piece.py`: ピース単体を管理するファイル．
* `src/proxy/piece_manager.py`: ピース全体を管理するファイル．
* `src/proxy/block.py`: ブロックを管理するファイル．
* `src/proxy/peer.py`: ピア単体を管理するファイル．
* `src/proxy/peer_manager.py`: ピア全体を管理するファイル．
* `src/proxy/message.py`: BitTorrentメッセージを処理するファイル．
* `src/proxy/torrent.py`: トレントファイル解析ファイル．
* `src/proxy/tracker.py`: トラッカー接続に関するファイル．
* `src/proxy/rarest_piece.py`: 希少ピースを探査するファイル．

#### proxy.py
Interestの受信を行う．受け取ったInterestの名前のピースが存在しない場合，`multiprocessing`で
`downloader.py`を開始し，BitTorrentピースの取得を行う．Queueで取得するピースを`downloader.py`に伝達する．
受け取ったInterestの名前のピースが存在すればピースをDataとして送信する．

#### downloader.py
BitTorrentによるピースの取得を行う．
インスタンス生成時にトレントファイルを解析する．
`def run()`が開始すると，トラッカーに接続し，ピア情報を受け取る．
ピアとハンドシェイクにより接続し， Queueに追加されたピースの取得を行う．

### 使用方法
ceforeを起動した状態で，以下のコマンドを実行することで起動する．
```angular2html
python3 proxy.py
```


<a id="Client"></a>
## Client

<a id="概要1"></a>
### 概要
ClientはBitTorrentのピースをCCNで要求するモジュールである．
以下のような機能を持つ．

* トレントファイルを解析
* トレントファイルを基にinfo_hashを計算
* `ccnx:/BitTorent/info_hash/piece/index` の名前で各ピースの要求を行う．
* 受け取ったDataを検証してファイルを完成させる．

<a id="構成1"></a>
### 構成
以下のファイルから構成される．

* `src/client/client.py`: トレントファイルを読み込み，コンテンツ取得を開始するファイル．
* `src/client/cefapp.py`: Interestを生成，送信するファイル．
* `src/client/piece.py`: ピース単体を管理するファイル．
* `src/client/piece_manager.py`: ピース全体を管理するファイル．
* `src/client/block.py`: ブロックを管理するファイル．
* `src/client/torrent.py`: トレントファイル解析ファイル．

#### client.py
トレントファイルの解析を行い，ピースの取得を開始する．

#### cefapp.py
ceforeにより，コンテンツのピースを取得するInterest生成・返ってきたDataを処理する．
パイプライン処理として，50ピースをあらかじめ要求しておく．1つのピースすべてのチャンクを同時に要求する．

<a id="使用方法1"></a>
### 使用方法
ceforeを起動した状態で，以下のコマンドを実行することで起動する．
```text
python3 client.py <トレントファイル.torrent>
```

<a id="lib"></a>
## lib
比較用BitTorrentクライアント


<a id="注意事項"></a>
## 注意事項
### 依存

cefore https://github.com/cefore/cefore.git 
キャッシュ機能使いたいから ./config --ebable-csmgr --enable-cache
※なぜか設定ファイルcefnetd.confでCS_MODEを0以外に設定するとファイル読み込めないと文句を言われる．
解決するためにdebugしてたところ，printfしただけで治った．謎だが同様のエラーが出る場合は下記のforkしたものの使用推奨

https://github.com/Marie673/cefore.git


cefpyco https://github.com/cefore/cefpyco
```text
bcoding==1.5
bitstring == 3.1.7
PyPubSub == 4.0.3
requests >= 2.24.0
pubsub == 0.1.2
ipaddress == 1.0.23
```
