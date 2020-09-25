# X-ray yield simulation (xys)

X 線収量を予測するための Python GUI コード。フォトンビームを標的に当て標的からの蛍光 X 線を測定する場合や線源からの X 線やガンマ線を測定する場合を想定している。
> これはモンテカルロシミュレーションではないので正確な値を求めるものではない。



## 必要なもの

 - Python 3 以上
 - [xraylib](https://github.com/tschoonj/xraylib)
 - PyQt5



## 原理

基本的には xraylib にまとめられている断面積の情報を使って物質内でのフォトンの透過や吸収そして蛍光を計算している。xraylib には[オンライン版](http://lvserver.ugent.be/xraylib-web/)もありますので、どのような物質に対してどのような情報を得られるのか見ておくと理解しやすい。

### 使っている断面積
- Transmission: 　　　　`CS_Total_CP`
- Absorption: 　　　　　`CS_Total_CP`
- PhotoElectric effect: 　`CS_Photo_CP`
- Fluorescence: 　　　　`CS_FluorLine_Kissel`

CP は Compound を指しており、compound parser で化合物の化学式と密度を定義できる。NIST で既に定義された化合物も利用できる (NIST compound)。化合物では元素比や質量比を考慮してある。

フォトンビームによる標的の蛍光を見る場合は**標的内での自己吸収**も考慮している。フォトンの入射角度と蛍光 X 線の取り出し角度を設定できるようにしてある (例えば 入射角 45°、取り出し角 45°)。

ここに必要な数式とか？




## 使い方
ターミナルで
`python xys_gui.py`
とすると GUI が立ち上がる。

左側のカラムにパラメータなどの設定項目がある。パラメータが固定であれば csv ファイルを読み込むことで設定することも可能で、自分がよく使うデフォルトの設定を選択できるようにしてある。主な設定項目は、**Detector**, **Target**, **Filter**, **RadioNucl**, **Beam** となっている。

![GUI 全体像](https://user-images.githubusercontent.com/10286550/94250985-3caa8300-ff22-11ea-9b36-392d7eb59f59.jpg)


