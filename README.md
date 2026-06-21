
# Options Calculator

<div align="center">

**[한국어](#한국어) | [English](#english) | [中文](#中文) | [日本語](#日本語)**

</div>

---

<a id="한국어"></a>

# 옵션 계산기

### 금융 투자자를 위한 강력한 옵션 전략 시뮬레이션 및 분석 도구

## 새로운 기능
- 회사명, 가격정보 및 그릭스의 디자인을 변경하였습니다 


<p align="center">
  <img width="800" alt="메인 화면" src="https://github.com/user-attachments/assets/9980e92c-fc72-49a1-aea5-41a27981b55f" />
</p>

<details open>
<summary><b>📊 스크린샷 더 보기</b></summary>
<p align="center">
  <img width="1660" alt="image" src="https://github.com/user-attachments/assets/9980e92c-fc72-49a1-aea5-41a27981b55f" />
  <br><br>
  <img width="1667" alt="image" src="https://github.com/user-attachments/assets/733ad5d4-8d30-448d-acc4-c83bf6e66e1e" />
  <br><br>
  <img width="1666" alt="image" src="https://github.com/user-attachments/assets/79551c01-8215-4fa3-9534-00c30679c6cc" />
  <br><br>
  <img width="1663" alt="image" src="https://github.com/user-attachments/assets/438a0b48-c3e6-4013-a339-b6abb4b69702" />
</p>
</details>



## 주요 기능

| 기능 | 설명 |
|------|------|
| **실시간 주식 데이터** | 주식 티커 심볼을 입력하여 실시간 주가 및 기본 정보 확인 |
| **옵션 전략 시뮬레이션** | 다양한 옵션 전략의 손익 구조를 시각화 |
| **그릭스 분석** | 델타, 감마, 베가, 세타, 로, 바나, 참 등 옵션 그릭스 계산 및 시각화 |
| **내재 변동성 분석** | 변동성 스마일/스큐 및 3D 변동성 표면 생성 |
| **Heston 모델 보정** | 옵션 체인으로 Heston stochastic volatility 파라미터를 보정하고 3D 이론가/오차 표면 표시 |
| **옵션 체인 조회** | 특정 만기일에 대한 전체 옵션 체인 데이터 확인 |
| **볼륨 차트 및 풋콜 비율** | 각 옵션의 볼륨 차트와 풋콜 비율 시각화 |
| **고급 그릭스 추가** | 고급 옵션 분석을 위한 Vanna와 Charm 그릭스가 추가되었습니다.|
| **전략 성과 분석** | 각 옵션 전략의 승률을 계산하여 표시합니다.|
| **확률 곡선 시각화** | 손익 구조 플롯에 전략의 다양한 결과에 대한 확률 분포 곡선을 추가합니다.|
| **향상된 옵션 가격 책정** | 옵션 이론 가격 계산에 52주 변동성 대신 델타 중립 내재 변동성을 사용합니다.|

## 사용 가능한 옵션 전략

<table>
  <tr>
    <td><b>단일(Single)</b></td>
    <td>기본 콜/풋 옵션 매수/매도</td>
  </tr>
  <tr>
    <td><b>커버드(Covered)</b></td>
    <td>커버드 콜(주식 매수 + 콜 매도) 또는 커버드 풋(주식 매도 + 풋 매도)</td>
  </tr>
  <tr>
    <td><b>보호(Protective)</b></td>
    <td>보호 풋(주식 매수 + 풋 매수) 또는 보호 콜(주식 매도 + 콜 매수)</td>
  </tr>
  <tr>
    <td><b>스프레드(Spread)</b></td>
    <td>콜/풋을 사용한 불/베어 스프레드</td>
  </tr>
  <tr>
    <td><b>스트래들(Straddle)</b></td>
    <td>동일 행사가의 콜과 풋 동시 매수/매도</td>
  </tr>
  <tr>
    <td><b>스트랭글(Strangle)</b></td>
    <td>서로 다른 행사가의 콜과 풋 동시 매수/매도</td>
  </tr>
  <tr>
    <td><b>스트립(Strip)</b></td>
    <td>동일 행사가에서 콜 1개, 풋 2개 매수 (베어리시 전략)</td>
  </tr>
  <tr>
    <td><b>스트랩(Strap)</b></td>
    <td>동일 행사가에서 콜 2개, 풋 1개 매수 (불리시 전략)</td>
  </tr>
  <tr>
    <td><b>버터플라이(Butterfly)</b></td>
    <td>제한된 위험과 보상의 3단계 전략</td>
  </tr>
  <tr>
    <td><b>래더(Ladder)</b></td>
    <td>일정 간격의 행사가를 가진 다중 단계 전략</td>
  </tr>
  <tr>
    <td><b>제이드 리저드(Jade Lizard)</b></td>
    <td>풋 매도 + 콜 스프레드 매도 (불리시 전략)</td>
  </tr>
  <tr>
    <td><b>리버스 제이드 리저드(Reverse Jade Lizard)</b></td>
    <td>풋 스프레드 매수 + 콜 매도 (베어리시 전략)</td>
  </tr>
  <tr>
    <td><b>콘도르(Condor)</b></td>
    <td>제한된 위험과 보상의 4단계 전략</td>
  </tr>
</table>

## 설치 및 실행

```bash
# 저장소 복제
git clone https://github.com/parkminhyung/Option_Calculator.git
cd Option_Calculator

# 필요한 패키지 설치
pip install streamlit pandas numpy yfinance plotly scipy

# 애플리케이션 실행
streamlit run app.py
```

## 사용 방법

1. 사이드바에 주식 티커 심볼을 입력하고 "Fetch Data" 버튼을 클릭합니다.

2. 원하는 옵션 전략, 행사가, 만기일 등의 파라미터를 설정합니다.

3. "Show Plot" 버튼을 클릭하여 전략의 손익 구조와 그릭스를 시각화합니다.

4. "Option Chain" 탭에서는 특정 만기일에 대한 옵션 체인 정보와 볼륨 차트, 풋콜 비율을 확인할 수 있습니다.

## 참고 사항

> **옵션 체인 정보와 볼륨 데이터는 yfinance 패키지에 의존하므로 일부 시장이나 종목에서는 데이터가 제한되거나 정확하지 않을 수 있습니다.**

> **Option Prices 하단에 나타나는 가격은 선택한 Pricing Model을 기반으로 도출한 이론가격입니다. 기본값은 델타 중립 내재 변동성을 사용하는 블랙숄즈모형입니다. 옵션 앞 +는 매수, -는 매도를 나타냅니다. 예를 들어 - call은 콜매도를 의미하며, +2x call은 콜을 2배로 매수한다는 뜻입니다.**

> **Heston 모델을 사용하려면 계산기 탭에서 Pricing Model을 Heston (calibrated)로 선택하고, Size 아래의 Calibrate Heston Now를 실행하세요. Option Chain 탭의 Heston Calibration 3D는 보정된 가격 표면과 오차를 시각적으로 확인하기 위한 선택 기능입니다. 보정 결과는 옵션 체인의 유동성, bid/ask 스프레드, 선택된 만기/행사가 범위에 크게 영향을 받습니다.**

---

<a id="english"></a>

# Options Calculator

### A powerful option strategy simulation and analysis tool for financial investors

## What's New
- The design of the company name, pricing information, and Greeks has been updated.

<p align="center">
  <img width="800" alt="Main Screen" src="https://github.com/user-attachments/assets/9980e92c-fc72-49a1-aea5-41a27981b55f" />
</p>

<details>
<summary><b>📊 More Screenshots</b></summary>
<p align="center">
  <img width="1660" alt="image" src="https://github.com/user-attachments/assets/9980e92c-fc72-49a1-aea5-41a27981b55f" />
  <br><br>
  <img width="1667" alt="image" src="https://github.com/user-attachments/assets/733ad5d4-8d30-448d-acc4-c83bf6e66e1e" />
  <br><br>
  <img width="1666" alt="image" src="https://github.com/user-attachments/assets/79551c01-8215-4fa3-9534-00c30679c6cc" />
  <br><br>
  <img width="1663" alt="image" src="https://github.com/user-attachments/assets/438a0b48-c3e6-4013-a339-b6abb4b69702" />
</p>
</details>

## Key Features

| Feature | Description |
|---------|-------------|
| **Real-time Stock Data** | Input a stock ticker symbol to get real-time prices and basic information |
| **Option Strategy Simulation** | Visualize the profit/loss structure of various option strategies |
| **Greeks Analysis** | Calculate and visualize option Greeks including Delta, Gamma, Vega, Theta, Rho, Vanna, and Charm |
| **Implied Volatility Analysis** | Generate volatility smiles/skews and 3D volatility surfaces |
| **Heston Calibration** | Calibrate Heston stochastic volatility parameters from option chains and display 3D theoretical price/error surfaces |
| **Option Chain Lookup** | View complete option chain data for specific expiry dates |
| **Volume Chart and Put-Call Ratio** | Visualize volume chart and put-call ratio for each option |
| **Advanced Greeks Added** | Vanna and Charm greeks have been added for sophisticated option analysis. |
| **Strategy Performance Analysis** Now calculates and displays the win rate for each option strategy. |
| **Probability Curve Visualization** | Added a probability distribution curve to the profit/loss plot for strategy outcomes. |
| **Enhanced Option Pricing** | Uses delta-neutral implied volatility instead of 52-week volatility for theoretical option pricing. |


## Available Option Strategies

<table>
  <tr>
    <td><b>Single</b></td>
    <td>Basic long/short positions in call/put options</td>
  </tr>
  <tr>
    <td><b>Covered</b></td>
    <td>Covered call (long stock + short call) or covered put (short stock + short put)</td>
  </tr>
  <tr>
    <td><b>Protective</b></td>
    <td>Protective put (long stock + long put) or protective call (short stock + long call)</td>
  </tr>
  <tr>
    <td><b>Spread</b></td>
    <td>Bull/bear spreads using calls or puts</td>
  </tr>
  <tr>
    <td><b>Straddle</b></td>
    <td>Long/short positions in both a call and put with the same strike</td>
  </tr>
  <tr>
    <td><b>Strangle</b></td>
    <td>Long/short positions in both a call and put with different strikes</td>
  </tr>
  <tr>
    <td><b>Strip</b></td>
    <td>Long 1 call and 2 puts at the same strike (bearish strategy)</td>
  </tr>
  <tr>
    <td><b>Strap</b></td>
    <td>Long 2 calls and 1 put at the same strike (bullish strategy)</td>
  </tr>
  <tr>
    <td><b>Butterfly</b></td>
    <td>A three-leg strategy with limited risk and reward</td>
  </tr>
  <tr>
    <td><b>Ladder</b></td>
    <td>A multi-leg strategy with strike prices at regular intervals</td>
  </tr>
  <tr>
    <td><b>Jade Lizard</b></td>
    <td>Short put + short call spread (bullish strategy)</td>
  </tr>
  <tr>
    <td><b>Reverse Jade Lizard</b></td>
    <td>Long put spread + short call (bearish strategy)</td>
  </tr>
  <tr>
    <td><b>Condor</b></td>
    <td>A four-leg strategy with limited risk and reward</td>
  </tr>
</table>

## Installation and Running

```bash
# Clone the repository
git clone https://github.com/parkminhyung/Option_Calculator.git
cd Option_Calculator

# Install required packages
pip install streamlit pandas numpy yfinance plotly scipy

# Run the application
streamlit run app.py
```

## How to Use

1. Enter a stock ticker symbol in the sidebar and click the "Fetch Data" button.

2. Set your desired parameters including option strategy, strike prices, expiry date, etc.

3. Click the "Show Plot" button to visualize the strategy's profit/loss structure and Greeks.

4. Use the "Option Chain" tab to view option chain information, volume charts, and put-call ratio for specific expiry dates.

## Notes

> **Option chain information and volume data depend on the yfinance package, so data may be limited or inaccurate for some markets or securities.**

> **The prices shown under Option Prices are theoretical prices based on the Black-Scholes model using delta-neutral implied volatility. The + sign in front of options indicates buying, while - indicates selling. For example, - call means selling a call, and +2x call means buying two call options.**

---

<a id="中文"></a>

# 期权计算器

### 为金融投资者提供的强大期权策略模拟和分析工具

## 新功能
- 更新公司名称、价格信息以及希腊值的设计。

<p align="center">
  <img width="800" alt="主屏幕" src="https://github.com/user-attachments/assets/9980e92c-fc72-49a1-aea5-41a27981b55f" />
</p>

<details>
<summary><b>📊 更多截图</b></summary>
<p align="center">
  <img width="1660" alt="image" src="https://github.com/user-attachments/assets/9980e92c-fc72-49a1-aea5-41a27981b55f" />
  <br><br>
  <img width="1667" alt="image" src="https://github.com/user-attachments/assets/733ad5d4-8d30-448d-acc4-c83bf6e66e1e" />
  <br><br>
  <img width="1666" alt="image" src="https://github.com/user-attachments/assets/79551c01-8215-4fa3-9534-00c30679c6cc" />
  <br><br>
  <img width="1663" alt="image" src="https://github.com/user-attachments/assets/438a0b48-c3e6-4013-a339-b6abb4b69702" />
</p>
</details>

## 主要功能

| 功能 | 描述발표자료 | 
|------|------|
| **实时股票数据获取** | 输入股票代码获取实时价格和基本信息 |
| **期权策略模拟** | 可视化各种期权策略的盈亏结构 |
| **希腊字母分析** | 计算并可视化期权希腊字母，包括Delta、Gamma、Vega、Theta、Rho、Vanna和Charm |
| **隐含波动率分析** | 生成波动率微笑/偏斜和3D波动率曲面 |
| **期权链查询** | 查看特定到期日的完整期权链数据 |
| **交易量图表和看跌/看涨比率** | 可视化每个期权的交易量图表和看跌/看涨比率 |
| **添加高级希腊字母** | 添加了Vanna和Charm高级希腊字母，用于复杂期权分析。|
| **策略表现分析** | 现在计算并显示每种期权策略的胜率。 |
| **概率曲线可视化** | 在损益图中添加了策略结果的概率分布曲线。 |
| **增强的期权定价** | 使用delta中性隐含波动率代替52周波动率进行理论期权定价。 |

## 可用期权策略

<table>
  <tr>
    <td><b>单一(Single)</b></td>
    <td>期权多空基本持仓</td>
  </tr>
  <tr>
    <td><b>备兑(Covered)</b></td>
    <td>备兑认购期权（买入股票+卖出认购期权）或备兑认沽期权（卖出股票+卖出认沽期权）</td>
  </tr>
  <tr>
    <td><b>保护(Protective)</b></td>
    <td>保护性认沽期权（买入股票+买入认沽期权）或保护性认购期权（卖出股票+买入认购期权）</td>
  </tr>
  <tr>
    <td><b>价差(Spread)</b></td>
    <td>使用认购期权或认沽期权的牛市/熊市价差策略</td>
  </tr>
  <tr>
    <td><b>跨式(Straddle)</b></td>
    <td>同时买入/卖出相同行权价的认购期权和认沽期权</td>
  </tr>
  <tr>
    <td><b>宽跨式(Strangle)</b></td>
    <td>同时买入/卖出不同行权价的认购期权和认沽期权</td>
  </tr>
  <tr>
    <td><b>看跌组合(Strip)</b></td>
    <td>在相同行权价买入1个认购期权和2个认沽期权（看跌策略）</td>
  </tr>
  <tr>
    <td><b>看涨组合(Strap)</b></td>
    <td>在相同行权价买入2个认购期权和1个认沽期权（看涨策略）</td>
  </tr>
  <tr>
    <td><b>蝶式(Butterfly)</b></td>
    <td>具有有限风险和回报的三腿策略</td>
  </tr>
  <tr>
    <td><b>阶梯(Ladder)</b></td>
    <td>具有等间距行权价的多腿策略</td>
  </tr>
  <tr>
    <td><b>翡翠蜥蜴(Jade Lizard)</b></td>
    <td>卖出认沽期权+卖出认购期权价差（看涨策略）</td>
  </tr>
  <tr>
    <td><b>反翡翠蜥蜴(Reverse Jade Lizard)</b></td>
    <td>买入认沽期权价差+卖出认购期权（看跌策略）</td>
  </tr>
  <tr>
    <td><b>秃鹰(Condor)</b></td>
    <td>具有有限风险和回报的四腿策略</td>
  </tr>
</table>

## 安装和运行

```bash
# 克隆仓库
git clone https://github.com/parkminhyung/Option_Calculator.git
cd Option_Calculator

# 安装所需包
pip install streamlit pandas numpy yfinance plotly scipy

# 运行应用
streamlit run app.py
```

## 使用方法

1. 在侧边栏输入股票代码并点击"Fetch Data"按钮。

2. 设置所需参数，包括期权策略、行权价、到期日等。

3. 点击"Show Plot"按钮可视化策略的盈亏结构和希腊字母。

4. 使用"Option Chain"标签页查看特定到期日的期权链信息、交易量图表和看跌/看涨比率。

## 注意事项

> **期权链信息和交易量数据依赖于yfinance包，因此某些市场或证券的数据可能有限或不准确。**

> **Option Prices下显示的价格是使用delta中性隐含波动率基于Black-Scholes模型的理论价格。期权前的+号表示买入，-号表示卖出。例如，-call表示卖出认购期权，+2x call表示买入两个认购期权。**

---

<a id="日本語"></a>

# オプション計算機

### 金融投資家のための強力なオプション戦略シミュレーションおよび分析ツール

## 新機能
- 会社名、価格情報、およびグリークスのデザインを変更しました。

<p align="center">
  <img width="800" alt="メイン画面" src="https://github.com/user-attachments/assets/9980e92c-fc72-49a1-aea5-41a27981b55f" />
</p>

<details>
<summary><b>📊 その他のスクリーンショット</b></summary>
<p align="center">
  <img width="1660" alt="image" src="https://github.com/user-attachments/assets/9980e92c-fc72-49a1-aea5-41a27981b55f" />
  <br><br>
  <img width="1667" alt="image" src="https://github.com/user-attachments/assets/733ad5d4-8d30-448d-acc4-c83bf6e66e1e" />
  <br><br>
  <img width="1666" alt="image" src="https://github.com/user-attachments/assets/79551c01-8215-4fa3-9534-00c30679c6cc" />
  <br><br>
  <img width="1663" alt="image" src="https://github.com/user-attachments/assets/438a0b48-c3e6-4013-a339-b6abb4b69702" />
</p>
</details>

## 主な機能

| 機能 | 説明 |
|------|------|
| **リアルタイム株式データ取得** | 株式ティッカーシンボルを入力してリアルタイム価格と基本情報を取得 |
| **オプション戦略シミュレーション** | 様々なオプション戦略の損益構造を視覚化 |
| **ギリシャ指標分析** | デルタ、ガンマ、ベガ、シータ、ロー、バンナ、チャームなどのオプションギリシャ指標を計算・視覚化 |
| **インプライドボラティリティ分析** | ボラティリティスマイル/スキューおよび3Dボラティリティサーフェスを生成 |
| **オプションチェーン検索** | 特定の満期日の完全なオプションチェーンデータを表示 |
| **ボリュームチャートとプット・コール比率** | 各オプションのボリュームチャートとプット・コール比率を視覚化 |
| **高度なギリシャ指標の追加** | 高度なオプション分析のためのVannaとCharmギリシャ指標が追加されました。 |
| **戦略パフォーマンス分析** | 各オプション戦略の勝率を計算して表示します。 |
| **確率曲線の視覚化** | 損益プロットに戦略結果の確率分布曲線を追加しました。 |
| **強化されたオプション価格設定** | 理論オプション価格の計算に52週ボラティリティの代わりにデルタ中立インプライドボラティリティを使用します。 |

## 利用可能なオプション戦略

<table>
  <tr>
    <td><b>シングル(Single)</b></td>
    <td>コール/プットオプションの基本的なロング/ショートポジション</td>
  </tr>
  <tr>
    <td><b>カバード(Covered)</b></td>
    <td>カバードコール（株式ロング+コールショート）またはカバードプット（株式ショート+プットショート）</td>
  </tr>
  <tr>
    <td><b>プロテクティブ(Protective)</b></td>
    <td>プロテクティブプット（株式ロング+プットロング）またはプロテクティブコール（株式ショート+コールロング）</td>
  </tr>
  <tr>
    <td><b>スプレッド(Spread)</b></td>
    <td>コールまたはプットを使用したブル/ベアスプレッド</td>
  </tr>
  <tr>
    <td><b>ストラドル(Straddle)</b></td>
    <td>同じ行使価格のコールとプットの両方をロング/ショート</td>
  </tr>
  <tr>
    <td><b>ストラングル(Strangle)</b></td>
    <td>異なる行使価格のコールとプットの両方をロング/ショート</td>
  </tr>
  <tr>
    <td><b>ストリップ(Strip)</b></td>
    <td>同じ行使価格でコール1つとプット2つをロング（ベアリッシュ戦略）</td>
  </tr>
  <tr>
    <td><b>ストラップ(Strap)</b></td>
    <td>同じ行使価格でコール2つとプット1つをロング（ブリッシュ戦略）</td>
  </tr>
  <tr>
    <td><b>バタフライ(Butterfly)</b></td>
    <td>限定されたリスクとリワードを持つ3レッグ戦略</td>
  </tr>
  <tr>
    <td><b>ラダー(Ladder)</b></td>
    <td>一定間隔の行使価格を持つマルチレッグ戦略</td>
  </tr>
  <tr>
    <td><b>ジェイドリザード(Jade Lizard)</b></td>
    <td>プットショート+コールスプレッドショート（ブリッシュ戦略）</td>
  </tr>
  <tr>
    <td><b>リバースジェイドリザード(Reverse Jade Lizard)</b></td>
    <td>プットスプレッドロング+コールショート（ベアリッシュ戦略）</td>
  </tr>
  <tr>
    <td><b>コンドル(Condor)</b></td>
    <td>限定されたリスクとリワードを持つ4レッグ戦略</td>
  </tr>
</table>

## インストールと実行

```bash
# リポジトリをクローン
git clone https://github.com/parkminhyung/Option_Calculator.git
cd Option_Calculator

# 必要なパッケージをインストール
pip install streamlit pandas numpy yfinance plotly scipy

# アプリケーションを実行
streamlit run app.py
```

## 使用方法

1. サイドバーに株式ティッカーシンボルを入力し、「Fetch Data」ボタンをクリックします。

2. オプション戦略、行使価格、満期日などの希望するパラメータを設定します。

3. 「Show Plot」ボタンをクリックして、戦略の損益構造とギリシャ指標を視覚化します。

4. 「Option Chain」タブを使用して、特定の満期日のオプションチェーン情報、ボリュームチャート、プット・コール比率を表示します。

## 注意事項

> **オプションチェーン情報とボリュームデータはyfinanceパッケージに依存しているため、一部の市場や証券ではデータが制限されたり正確でない場合があります。**

> **Option Prices下に表示される価格はデルタ中立インプライドボラティリティを使用してブラック・ショールズモデルに基づく理論価格です。オプションの前の+は買い、-は売りを示します。例えば、- callはコールの売りを意味し、+2x callはコールを2倍買うことを意味します。**
