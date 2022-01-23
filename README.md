# Torrent_Proxy
仮で書いているためraw dataで見た方が見やすい


ソースファイルはsrc/に格納

lib 通常のBitTorrentクライアント
threadingでソケット通信 受信送信共に

proxy プロキシ Interestを受信するとそのコンテンツのすべてのピースを要求 データサイズが大きいとメモリが書き換えられるのでファイルシステム
ceforeの受信がメインプロセス
Interest受信後にmultiprocessingでBitTorrentダウンロード開始 
BitTorrentのメッセージはthreading
multiprocessing.Managerを使用しピースを管理

proxy_type1 受信したInterestのピースのみダウンロード ピースをずっと保持している必要はないのでメモリに保管
Interest受信後にmultiprocessingでBitTorrentダウンロード開始
同時にQueue監視用thread処理も開始
BitTorrentのメッセージ受信はthreading
ピースが完成するとQueueでメインプロセスに通知
QueueにputされるとメインプロセスはData送信

client CCNで使用するbittorrentクライアント ピースの管理方法はilbで記述したものと一緒 ブロック単位での要求ではなくピース単位での要求 所持していないピースのInterestをすべて送信 
Interestのlifetimeを3秒に設定しているのでInterestの送信は3秒毎 udpのためInterestは3通同時送信()
threadingでceforeのメッセージ管理

プログラム毎で時間計測 最初の要求を出した時点で計測開始 すべてのピースが手に入ると(ファイルが完成すると：ピースの検証完了まで)計測終了


tc/はtcコマンドのbash

lient1 client3は帯域制限のみ 100Mbps
client2は帯域制限と遅延 100Mbps 10ms


test/に実験に使用したtorrentファイル格納

ファイルはddにより作成
ex.)dd if=/dev/zero of=1G.dummy bs=1M count=1024

ceforeはバッファチューンしろと書いていたのでそれ用のbashコマンドbuffa_tune.sh


依存
cefore https://github.com/cefore/cefore.git 
キャッシュ機能使いたいから ./config --ebable-csmgr --enable-cache
※なぜか設定ファイルcefnetd.confでCS_MODEを0以外に設定するとファイル読み込めないと文句を言われる．
解決するためにdebugしてたところ，printfしただけで治った．謎だが同様のエラーが出る場合は下記のforkしたものの使用推奨

https://github.com/Marie673/cefore.git


cefpyco https://github.com/cefore/cefpyco

bcoding==1.5
bitstring == 3.1.7
PyPubSub == 4.0.3
requests >= 2.24.0
pubsub == 0.1.2
ipaddress == 1.0.23
後でrequirement書く
