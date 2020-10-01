# X-ray yield simulation (xys)

特性 X 線収量を予測するための Python GUI コード。フォトンビームを標的に当て標的からの蛍光 X 線を測定する場合や線源からの X 線やガンマ線を測定する場合を想定している。
> これはモンテカルロシミュレーションではないので正確な値を求めるものではない。



## 必要なもの

 - Python 3 以上
 - [xraylib](https://github.com/tschoonj/xraylib)
 - PyQt5


## 使い方
### 起動

ターミナルで

`python xys_gui.py`

とすると下のような GUI が立ち上がる。

![GUI 全体像](https://user-images.githubusercontent.com/10286550/94250985-3caa8300-ff22-11ea-9b36-392d7eb59f59.jpg)

### 入力

左側のカラムにパラメータなどの設定項目がある。パラメータが固定であれば csv ファイルを読み込むことで設定することも可能で、自分がよく使うデフォルトの設定を選択できるようにしてある。主な設定項目は、**Detector**, **Target**, **Filter**, **RadioNucl**, **Beam** となっている。

**Detector**, **Target**, **Filter** は大体同じような構成で、Element, NIST compound, Compound parser で物質と厚さ Thickness (cm) を決め、必要なら密度 Density (g/cm3) を入力し、**Add** で選択した物質を追加、**Remove** で削除、**Reset** ですべて削除する。ただし **Target** に関しては一つのみを想定しているので **Add** ではなく **Set** にしてある。物質を **Add/Set** すると中央のカラムにある **Current setting** に反映される。**Target** の場合はその蛍光 X 線の詳細が中央カラムの **X-ray lines** にも反映される。

**RadioNucl** は線源からの X 線やガンマ線の測定を想定している。線源を選択してキャリブレーションされた年月日 Date calib と放射能強度 Activity calib (Bq) を入力すると、本日の放射能強度を計算できる。測定時間 Duration time を入力すると測定強度にリニアに反映される。エラー回避のため初期値としてキャリブレーション日時を 20110311, 強度を1e6 Bq, Duration time 3600 sec としてある。線源を **Add** すると中央カラムの **X-ray lines** に反映される。線源は複数選択できる。

**Beam** はフォトンによる標的の励起を想定している。ここでは放射光のように単一エネルギーのフォトンを想定しているが、X 線管のような広いエネルギー分布をもつ X 線源を用いて、あるエネルギーだけに注目した場合と考えてもよい。パラメータは Incident energy (keV), Beam flux (photons/sec), Incident angle (degree), Outgoing angle (degree), Beam time (sec) で、エラー回避のためにテキトウな初期値が入力してある。**Set** を押すと反映されるが、**Plot** 時に値を取りに行くので押し忘れは気にしなくてもよいかもしれない。エラー回避のため**Reset** を押してもゼロにならない仕様である。

### Plot

必要な情報を入力したあとに **Plot** を押すと下のように2つの図が得られる。上の図は Filter による X 線の Transmission と Detector による Absorption の割合を示していて、黒いカーブがその掛け算で最終的な量子効率となる。

![plot_xys](https://user-images.githubusercontent.com/10286550/94258180-bf384000-ff2c-11ea-9386-c19a647b15d3.jpg)

下の図は予想される X 線のエネルギースペクトルである。ピークは (いまのところ) Voigt 関数で、エネルギーとその自然幅は xraylib から得ている。`line_wrap.py` ファイルに `voigt`, `get_linewidth`,`get_lineenergy` があるので参照して欲しい。測定器のエネルギー分解能は指定でき ON/OFF 切替可能で、Plot の下にある Detector resolution FWHM (eV) のチェックボックスで制御できる。**ただし分解能のエネルギー依存性は考慮していない**。

Energy range の設定は Low, High を入力してその間の Step を keV 単位で入力する。あまり小さな step にするとプロットする点の数が大きくなるので重くなることが予想される。

測定器の立体角は Solidangle ratio で 0 から 1 の実数を入力する。これは X 線の強度にリニアに効いてくる。

### Save

**Save** ボタンを追加した (2020 Sep 29)。**Plot** してから **Save** を押すと保存できる。とりあえず、エネルギー範囲を **Step** (keV) で指定した間隔に対する quantum efficiency (`qe.txt`) と fluorescence (`fluor.txt`) を ascii として `./output` ディレクトリに出力する。ファイル名は `_001.txt`, `_002.txt` と連番で増えていくようにしてある (あまり深くは考えていない)。エネルギー範囲が広くて **Step** が細かいとファイルサイズが大きくなるので注意。同様に **Plot** の 図の PDF ファイルも保存されるようにした。

> Plot 用にエネルギー範囲を狭くしたけど ascii データは 0-20 keV の間隔で欲しい、という場合があると思うが (原理的にはできるとけどなんかめんどくさそう) 今はとりあえずデータ用と plot 用で範囲を変えて save して対応して欲しい。


## 原理

基本的には xraylib にまとめられている断面積の情報を使って物質内でのフォトンの透過や吸収そして蛍光を計算している。xraylib には[オンライン版](http://lvserver.ugent.be/xraylib-web/)もあるので、どのような物質に対してどのような情報を得られるのか見ておくと理解しやすい。

### 使っている断面積
- Transmission: 　　　　`CS_Total_CP`
- Absorption: 　　　　　`CS_Total_CP`
- PhotoElectric effect: 　`CS_Photo_CP`
- Fluorescence: 　　　　`CS_FluorLine_Kissel`

CP は Compound を指しており、compound parser で化合物の化学式と密度を定義できる。NIST で既に定義された化合物も利用できる (NIST compound)。化合物では元素比や質量比を考慮してある。

詳しい原理は以下の PDF ファイルに記した。
[xys.pdf](https://github.com/hidet/xys/blob/master/xys.pdf)
