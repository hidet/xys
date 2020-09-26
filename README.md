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

<<<<<<< HEAD
測定器の立体角は Solidangle ratio で 0 から 1 の実数を入力する。これは X 線の強度にリニアに効いてくる。
=======
**Beam** はフォトンによる標的の励起を想定している。ここでは放射光のように単一エネルギーのフォトンを想定しているが、X 線管のような広いエネルギー分布をもつ X 線源を用いて、あるエネルギーだけに注目した場合と考えてもよい。パラメータは Incident energy (keV), Beam flux (photons/sec), Incident angle (dgree), Outgoing angle (degree), Beam time (sec) で、エラー回避のためにテキトウな初期値が入力してある。**Set** を押すと反映されるが、**Plot** 時に値を取りに行くので押し忘れは気にしなくてもよいかもしれない。エラー回避のため**Reset** を押してもゼロにならない仕様である。
>>>>>>> fa3a412e8ab2831d15a63ca364ce89c6ebeee1e4

## 原理

基本的には xraylib にまとめられている断面積の情報を使って物質内でのフォトンの透過や吸収そして蛍光を計算している。xraylib には[オンライン版](http://lvserver.ugent.be/xraylib-web/)もあるので、どのような物質に対してどのような情報を得られるのか見ておくと理解しやすい。

### 使っている断面積
- Transmission: 　　　　`CS_Total_CP`
- Absorption: 　　　　　`CS_Total_CP`
- PhotoElectric effect: 　`CS_Photo_CP`
- Fluorescence: 　　　　`CS_FluorLine_Kissel`

CP は Compound を指しており、compound parser で化合物の化学式と密度を定義できる。NIST で既に定義された化合物も利用できる (NIST compound)。化合物では元素比や質量比を考慮してある。

### Transmission / Absorption
フォトンの透過の割合を計算するには **mass attenuation coefficients** $\mu/\rho$ (cm2/g) を使って$$\exp{[-(\mu/\rho)\rho t]}$$とかける。ここで $\rho$ は物質の密度 (g/cm3), $t$ は厚さ (cm) である。密度で割っているのを明示するために $\rho$ を書いているが、単に $\mu$ とかく場合もあるので単位には注意が必要。
吸収の割合は 1 から透過の割合を引けばよいので $$1-\exp{[-(\mu/\rho) \rho t]}$$ とかける。xraylib では **total attenuation cross section** `CS_Total_CP` となっているが、単位的には $\mu/\rho$ の値を採用していて、両者には次の関係がある $$\mu/\rho = \sigma_{\rm{tot}}/uA$$ ここで $u$ は atomic mass unit (1.660 540 2$\times 10^{-24}$ g), $A$ は標的元素の相対質量である。$\sigma_{\rm{tot}}$ の単位は cm2/atom になる。ちなみに `CSb_Total_CP` を使えば barn/atom 単位の断面積が得られる。

化合物の場合は $i$ 番目の元素の mass fraction $w_i$ を用いて $$\mu/\rho = \sum_i w_i (\mu/\rho)_i$$ とかける。

### PhotoElectric Effect
X 線のエネルギー領域では、光電効果は主に測定器内でのエネルギー吸収と考えてよいのでフォトンの吸収として計算する。先程の $\sigma_{\rm{tot}}$ には光電効果の断面積 $\sigma_{\rm{ph}}$ が含まれていて、xraylib ではその光電効果の部分 $(\mu/\rho)_{\rm{ph}}$ だけを `CS_Photo_CP` でとってくることができる。計算は吸収なので $$1-\exp{[-(\mu/\rho)_{\rm{ph}} \rho t]}$$ となる。

### X-ray Fluorescence
フォトンによる励起後に X 線を放出し脱励起する現象を記述する。ここではある X 線の **fluorescence cross section** として xraylib の `CS_FluorLine_Kissel` を採用した。ある元素の K$_{\alpha1}$ X 線の fluorescence cross section は次のように定義できる $$Q_{K_{\alpha1}} = \sigma_K \omega_K R_{K_{\alpha1}}$$ ここで、$\sigma_K$ は光電効果で K-shell を励起する断面積 (cm2/g)、$\omega_K$ は電子が K-shell へ遷移するときに X 線を出す割合 fluorescence yield, $R_{K_{\alpha1}}$ は放出される X 線が K$_{\alpha1}$ である割合 radiative rate である。つまりこの3つの物理量を一つにまとめたものとして使っている。
> 最近では xraylib に cascade を考慮した fluorescence cross section が導入されており、`CS_FluorLine_Kissel_Cascade`, `CS_FluorLine_Kissel_Nonradiative_Cascade`, `CS_FluorLine_Kissel_Radiative_Cascade`, `CS_FluorLine_Kissel_no_Cascade` を使うことができる。`CS_FluorLine_Kissel` は `CS_FluorLine_Kissel_Cascade` と同じもの。

フォトンビームによる標的の蛍光を見る場合は**標的内での自己吸収**も考慮しなければならない。フォトンビームの入射角度 $\alpha$, 蛍光 X 線の取り出し角度 $\beta$ (これらは **Beam** のタブで設定できる) としたとき、測定器に入る標的 $i$ 番目元素の K$_{\alpha1}$ X 線の fluorescence は次のようにかける $$I_{i,K_{\alpha1}} = I_0 \frac{\Omega}{4\pi} w_i Q_{i,K_{\alpha1}} \rho t \left(\frac{1-\exp{(-\chi\rho t)}}{\chi\rho t}\right) $$ $$\chi = \frac{\sum_{k=1}^n w_k (\mu/\rho)_{k}(E_0)}{\sin{\alpha}} + \frac{\sum_{k=1}^n w_k (\mu/\rho)_{k}(E_{K_{\alpha1}})}{\sin{\beta}}$$ ここで $I_0$ は入射フォトン強度, $\Omega$ は測定器の立体角, $w_i$ は $i$ 番目元素の mass fraction, $Q_{i,K_{\alpha1}}$ は $i$ 番目元素の K$_{\alpha1}$ X 線の fluorescence cross section, $\rho$ は標的密度, $t$ は標的の厚さ, $(\mu/\rho)_k (E)$ は $k$ 番目元素のエネルギー $E$ における mass attenuation coefficients で、$\sum_{k=1}^n$ は標的化合物全体を表している。後ろの括弧内の表記だけではあまりにも不親切なので、できるだけ計算の詳細を以下に記しておく。

csv ファイルについて ... 更新予定
