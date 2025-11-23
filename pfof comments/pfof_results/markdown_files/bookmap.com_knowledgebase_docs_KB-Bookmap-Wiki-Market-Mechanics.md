---
                title: "('Market Mechanics · Bookmap Knowledge Base',)"
                url: "https://bookmap.com/knowledgebase/docs/KB-Bookmap-Wiki-Market-Mechanics"
                date: ""
                sentiment: "('Neutral',)"
                topic: "pfof"
                ---

                

[Skip to main content](#__docusaurus_skipToContent_fallback)
[![](/knowledgebase/img/Bookmap_logo.png)![](/knowledgebase/img/Bookmap_logo.png)

**Bookmap Knowledge Base**](https://bookmap.com)[User Guide](/knowledgebase/docs/KB-Welcome)[Add-ons](/knowledgebase/docs/Addons-SIT)[API](/knowledgebase/docs/API)

[English](/knowledgebase/docs/KB-Bookmap-Wiki-Market-Mechanics)

* [English](/knowledgebase/docs/KB-Bookmap-Wiki-Market-Mechanics)
* [Deutsch](/knowledgebase/de/docs/KB-Bookmap-Wiki-Market-Mechanics)
* [Italiano](/knowledgebase/it/docs/KB-Bookmap-Wiki-Market-Mechanics)
* [Français](/knowledgebase/fr/docs/KB-Bookmap-Wiki-Market-Mechanics)
* [Español](/knowledgebase/es/docs/KB-Bookmap-Wiki-Market-Mechanics)
* [Português](/knowledgebase/pt/docs/KB-Bookmap-Wiki-Market-Mechanics)
* [Nederlands](/knowledgebase/nl/docs/KB-Bookmap-Wiki-Market-Mechanics)
* [Türkçe](/knowledgebase/tr/docs/KB-Bookmap-Wiki-Market-Mechanics)
* [हिन्दी](/knowledgebase/hi/docs/KB-Bookmap-Wiki-Market-Mechanics)


Search


* [1. Introduction to Bookmap](/knowledgebase/docs/KB-Welcome)
* [2. Getting Started](/knowledgebase/docs/KB-GettingStarted-SubscribeDownload)
* [3. Setting Up & Operating Bookmap](/knowledgebase/docs/KB-SettingUpAndOperating-Tabs)
* [4. Trading](/knowledgebase/docs/KB-Trading-Trading)
* [5. Indicators](/knowledgebase/docs/KB-Indicators-DisplaySettings)
* [6. Multibook](/knowledgebase/docs/KB-Multibook-Introduction)
* [7. Strategies](/knowledgebase/docs/KB-Automated-Strategies)
* [8. Partnerships](/knowledgebase/docs/KB-TOS-Introduction)
* [9. Bookmap Wiki](/knowledgebase/docs/KB-Bookmap-Wiki-Iceberg-Orders-Tracker)
+ [Iceberg Orders Tracker](/knowledgebase/docs/KB-Bookmap-Wiki-Iceberg-Orders-Tracker)
+ [Market Mechanics](/knowledgebase/docs/KB-Bookmap-Wiki-Market-Mechanics)
* [10. Advanced Solutions](/knowledgebase/docs/KB-AdvancedSolution-Bookmap-Quant-Solution-Setup)
* [11. Help](/knowledgebase/docs/KB-Help-FAQs-Basics)
* [12. Errors](/knowledgebase/docs/KB-Errors-General-Errors-And-Crashes)
* [13. Appendices](/knowledgebase/docs/KB-Appendices-AI-KeyboardHotkeys)


* 9. Bookmap Wiki
* Market Mechanics
On this page

**Market Mechanics** describe what are orders, the microstructure, and the dynamics of order book/order flow inside exchanges (or trading venues). It shows how matching engines use various matching algorithms to process the orders, and how it is reflected in the market data that they generate. This article is a 'crash course' on Market Mechanics, brief, but intense. It doesn't require any background knowledge in trading and it doesn't assume a specific market, making it suitable for Futures, Stocks, Cryptocurrency, and so on.

![screenshot](/knowledgebase/assets/images/001_Exchange_and_traders-27de5e871effa8097eacfe0468ed544e.png "X-Change & Traders")

Why should I read it?[​](/knowledgebase/docs/KB-Bookmap-Wiki-Market-Mechanics#why-should-i-read-it "Direct link to Why should I read it?")
------------------------------------------------------------------------------------------------------------------------------------------

![screenshot](/knowledgebase/assets/images/002_Screenshot_ES-3f65ee02601523d3097621392e29dbff.png "ES")

There is a number of reasons why it's recommended to understand market mechanics before starting to trade or developing a trading strategy. Here are some of them.

Market Mechanics Trading Approach[​](/knowledgebase/docs/KB-Bookmap-Wiki-Market-Mechanics#market-mechanics-trading-approach "Direct link to Market Mechanics Trading Approach")
-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

Understanding market mechanics is more than theory. Traders can build strategies around how orders are placed, matched, and executed. This trading approach helps frame the market as a system of rules and actions, allowing traders to anticipate reactions rather than relying only on price charts.

#### The price is determined by orders of traders[​](/knowledgebase/docs/KB-Bookmap-Wiki-Market-Mechanics#the-price-is-determined-by-orders-of-traders "Direct link to The price is determined by orders of traders")

**Price, traded volume, and all thousands of market-data-based indicators are all 100% determined by the actions of traders and nothing else.** Once an action reaches the exchange and assuming that it is valid, it is processed by a matching engine using a predefined, public, and deterministic matching algorithm. The result of this process may or may not lead to an execution, but it must always lead to an update of the order book. Consequently, exchange generates corresponding market data, still in some deterministic way based on what happened. Therefore, any market data-based indicator including the price itself (in the form of best Bid/Ask, Last Trade, or anything else) is determined by the actions of traders.

#### Price modeling vs orders modeling[​](/knowledgebase/docs/KB-Bookmap-Wiki-Market-Mechanics#price-modeling-vs-orders-modeling "Direct link to Price modeling vs orders modeling")

Many trading strategies and studies are based on mathematical modeling of price behavior, including the usage of [random walk](https://en.wikipedia.org/wiki/Random_walk) models. But since the price is a direct function of orders, modeling the behavior of orders can be more fruitful, including modeling a random market by using random orders which represent uninformed traders. This is because the same action, e.g. buy 1000 units at market price, can lead to different results depending on the current state of the order book, i.e. previously sent actions. As a bonus, such modeling of the market allows greater flexibility while still being simple.

Trading Strategy Based on Market Mechanics[​](/knowledgebase/docs/KB-Bookmap-Wiki-Market-Mechanics#trading-strategy-based-on-market-mechanics "Direct link to Trading Strategy Based on Market Mechanics")
----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

A trading strategy grounded in market mechanics focuses on the order book, matching algorithms, and trader actions. For example, analyzing how aggressive orders consume liquidity can help in timing short-term trades.

* Scalpers may watch queue position and speed of execution.
* Swing traders may focus on how resting liquidity accumulates around key levels.

This bridges the theory of market microstructure with practical application.

### Wars do not affect the market[​](/knowledgebase/docs/KB-Bookmap-Wiki-Market-Mechanics#wars-do-not-affect-the-market "Direct link to Wars do not affect the market")

..., i.e. not directly. Any events, whether scheduled or unscheduled, anywhere on Earth or outside can affect only the decisions of traders, their actions, and as a result -- the market. This is why observing via the market data the actions of those who are the first to respond, such as Market Makers and high-frequency traders (HFT) in general, is in a sense the fastest global news feed [[1]](https://twitter.com/bookmap_pro/status/991806902324662272).

### There are no 'macro' events in the market[​](/knowledgebase/docs/KB-Bookmap-Wiki-Market-Mechanics#there-are-no-macro-events-in-the-market "Direct link to There are no 'macro' events in the market")

... i.e. formally, any macro event is a cumulative effect of micro-events - the orders of traders, which are processed by exchanges typically in microseconds. Long-term investors may use monthly candlesticks to analyze the major price movements over the last decade. Understandably, they don't need to analyze terabytes of raw market data during that period. But it's useful to know that if they decide to process such data, they would calculate exactly the same monthly candlesticks. It's just that someone else already did it for them.

### Put your money where your mouth is[​](/knowledgebase/docs/KB-Bookmap-Wiki-Market-Mechanics#put-your-money-where-your-mouth-is "Direct link to Put your money where your mouth is")

This saying, although a little rude, has a basis. Market data is always a history. Traders watch it to make a prediction about the future. Even if they watch it to develop a trading strategy, the purpose is to be able to make a better prediction in the future. That includes all types of traders from long-term investors to HFT. But since market data is generated by the activity of traders, observing it is in a sense, an attempt to understand what other traders think about the future.

It’s reasonable and supported by pieces of evidence that when people bet on future events with real money, their biased views and wishful thinking have a lower impact on their decisions [[2]](https://www.youtube.com/watch?v=Qjx9WO_YTyU). Such betting systems provide a more accurate prediction than polls even for hardly predictable political events or the results of football games. Observing these risk-taking votes allows even non-participants to understand better what do participants think about the future and to filter out potential bias or wishful thinking.

The analogy with markets is straightforward: these risk-taking voters are traders who actually place orders (unlike, for instance, educators and commentators who don't). But in regards to trading, this method of truth extraction is much more powerful because, unlike football fans, traders actually play and thus affect the price. Moreover, as shown above, traders are the only ones who affect it. That also includes manipulation and deception tactics by large traders. In fact, it's the reason why such tactics are being used -- exactly because they affect the market. But they affect it indirectly, through the actions of other traders who observe them. Unlike fake large orders, real orders affect the market directly.

### Know the rules of the game[​](/knowledgebase/docs/KB-Bookmap-Wiki-Market-Mechanics#know-the-rules-of-the-game "Direct link to Know the rules of the game")

![screenshot](/knowledgebase/assets/images/003_DIKW-72734051f6ae2424c2def99da2bc2010.png "DIKW")

Trading is a multiplayer real-time game. Like in most such games, there are winners and losers, but that competitiveness is what makes such games interesting. In trading, the rules are determined by exchanges in the form of matching algorithms and sometimes different latency priorities. These rules may favor certain types of market participants such as registered Market Makers by offering them higher matching priorities or even by adding artificial speed bumps for other traders (scroll down for Latency). But these rules can be considered fair simply because they are public. Traders who know the rules of the game can adjust their trading strategy accordingly, or walk away to markets with better rules, or decide not to trade at all.

How to Trade Using Market Mechanics[​](/knowledgebase/docs/KB-Bookmap-Wiki-Market-Mechanics#how-to-trade-using-market-mechanics "Direct link to How to Trade Using Market Mechanics")
-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

Trading with market mechanics involves applying knowledge of exchange rules, order types, and latency. By knowing how the matching engine prioritizes orders, traders can decide whether to act as a market taker or a market maker. Understanding these mechanics gives traders an edge in execution and risk control.

Factors for success in trading[​](/knowledgebase/docs/KB-Bookmap-Wiki-Market-Mechanics#factors-for-success-in-trading "Direct link to Factors for success in trading")
----------------------------------------------------------------------------------------------------------------------------------------------------------------------

There is a number of factors that make trading more successful, such as:

* Having an access to high-quality data
* Ability to convert available data into information and knowledge using strong infrastructure, analytical tools, and high-quality visualization
* Wisdom to develop effective tactics based on knowledge, the ability to predict future events (including one's own impact), and to manage the risks
* Speed of data processing and execution of actions, i.e. latency and infrastructure
* A brute force that can simply move the market in the desired direction

Together, these factors give an even stronger competitive advantage than a sum of them because they complement each other and depend on each other. For instance, fast execution of a wrong prediction of price direction leads to a worse execution price than slow execution of the same decision.

How to Analyze Market Mechanics[​](/knowledgebase/docs/KB-Bookmap-Wiki-Market-Mechanics#how-to-analyze-market-mechanics "Direct link to How to Analyze Market Mechanics")
-------------------------------------------------------------------------------------------------------------------------------------------------------------------------

Analysis starts with observing how orders enter, rest, and get executed in the book. Key elements include:

* Matching algorithms (FIFO, Pro-Rata).
* Commission structures for makers vs takers.
* Latency effects during bursts of activity.

By breaking down these moving parts, traders learn how market dynamics unfold in real time.

Orders[​](/knowledgebase/docs/KB-Bookmap-Wiki-Market-Mechanics#orders "Direct link to Orders")
----------------------------------------------------------------------------------------------

Orders are the most basic elements in trading, but at the same time, as shown above, the only elements that affect the market. An order is a set of parameters defined by traders.

**Market order** is the most basic type of order and has just two parameters:

* **Buy or Sell**
* **Size**

All other types of orders inherit the definition of Market order and extend it with additional parameters.

**Limit order**, the most frequently used type of order, adds the price parameter:

* **Price** (this instructs the exchange that the order must not be executed at a worse price than specified)

**Iceberg order** adds another parameter:

* **Maximum displayed size** (The tip of the iceberg, instructs the exchange not to display more than specified of the total order size)

*See also:* [Stops & Icebergs On-Chart Indicator](https://bookmap.com/knowledgebase/docs/Addons-Stops-And-Icebergs-On-Chart-Indicator) and [Stops & Icebergs Sub-Chart Indicator](https://bookmap.com/knowledgebase/docs/Addons-SIT)

**Stop order** is a conditional order. It adds a condition parameter:

* **Stop price** (instructs the exchange to publish/release the order only if a trade occurs at equal or worse than the specified price)

### Examples of Market Mechanics Trading Strategies[​](/knowledgebase/docs/KB-Bookmap-Wiki-Market-Mechanics#examples-of-market-mechanics-trading-strategies "Direct link to Examples of Market Mechanics Trading Strategies")

Examples include:

* Fading liquidity when large resting orders are repeatedly tested but not consumed.
* Joining momentum when aggressive orders sweep multiple price levels quickly.
* Exploiting maker vs taker fee differences in high-volume markets.

There are many other types of either instant or conditional orders which use additional parameters including time-in-force (TiF) that tells the exchange when the order can be published/released, chains of orders, and so on. Exchanges may offer to traders additional types of orders with any level of customization. Intermediate parties such as brokers and order management systems (OMS) may offer even more flexibility while managing the orders in the exchange co-located facilities which allows sub-millisecond response time.

### Actions of traders[​](/knowledgebase/docs/KB-Bookmap-Wiki-Market-Mechanics#actions-of-traders "Direct link to Actions of traders")

The set of actions available to traders didn't change significantly over centuries and probably millenniums since the first sort of trading venue was established. What has changed significantly is the speed in which these actions can be delivered to the exchange and the speed at which exchanges process them and provide corresponding feedback. Also, market data has changed significantly, mainly because of improved technology & bandwidth. Market data today allow much greater market transparency.

The exact list of actions that are available to traders and their parameters is defined by exchanges, but typically there are just two or three of them. Assuming regular limit orders, it looks like this:

![screenshot](/knowledgebase/assets/images/004_Actions_of_Traders_A-80e70620b1486a304413fbac2e162a11.png "Actions of Traders")

Actions can be rejected due to insufficient funds, invalid parameters, or if referenced order doesn't exist anymore (canceled or executed), etc. Additional responses of exchange include updates of orders' status such as partial or full execution, cancellation confirmation, and so on. Also, most exchanges but not all (e.g. not supported by GDAX exchange) allow order modification as follows:

![screenshot](/knowledgebase/assets/images/004_Actions_of_Traders_B-ad51519b2d3a2ab8b57670349c71f61b.png "Actions of Traders")

Order modification is in a sense a redundant action because it can be replaced by canceling the order and sending a new one. But modify action allows to reduce the latency because both of its sub-actions are performed instantly in the exchange and allows to avoid the risk of undesired exposure due to the in-flight condition: for instance if trader sends a pair of actions to cancel/send when they reach the exchange the order may already be executed, but the new order can still be accepted. Also, if the requested modification only reduces the order size within the same price, the order keeps its position in the orders queue.

Order Book[​](/knowledgebase/docs/KB-Bookmap-Wiki-Market-Mechanics#order-book "Direct link to Order Book")
----------------------------------------------------------------------------------------------------------

Order book is a collection of orders of traders, constructed by matching engines of exchanges. It consists of:

* Visible in market data collection of limit buy and sell orders (the order book). These orders are resting in the order book because their limit price didn't permit yet their match/execution
* Invisible in market data conditional orders. These orders have a certain trigger or condition to be published/released by the exchange and to become visible.

The collection of orders at the same price level is called an order queue. Orders can advance in the queue when other orders in front of them are canceled or executed/matched with new arriving orders. The arrangement of orders in the queue and the priority of their execution is determined by the matching algorithm as will be shown further.

![screenshot](/knowledgebase/assets/images/005_Order_Book-9f49f57776b0b3f4bae48b5445a71f9f.png "Order Book")

Market Data types[​](/knowledgebase/docs/KB-Bookmap-Wiki-Market-Mechanics#market-data-types "Direct link to Market Data types")
-------------------------------------------------------------------------------------------------------------------------------

The order book changes only when traders conduct new actions or if conditional orders are released according to their time-in-force settings. Consequently, exchanges generate market data and inform traders about what has changed. Today there are two main distinct types of market data.

### Market by Price[​](/knowledgebase/docs/KB-Bookmap-Wiki-Market-Mechanics#market-by-price "Direct link to Market by Price")

**Market-by-Price (MBP)** describes a price-based data feed that provides the ability to view the total size of all orders at each price level. MBP can describe either full market depth or a limited number of nearest Bid and Ask price levels, e.g. 5, 10, or 20 price levels.

### Market by Order[​](/knowledgebase/docs/KB-Bookmap-Wiki-Market-Mechanics#market-by-order "Direct link to Market by Order")

Market-by-Order (MBO) or Order-by-Order describes an order-based data feed that provides the ability to view individual orders and their evolution. The order's information contains its unique Order ID, limit price, size, and its location in the queue. MBO typically provides full market depth, describing orders at each price level. This is the more modern and more transparent type of market data.

### Other types of market data[​](/knowledgebase/docs/KB-Bookmap-Wiki-Market-Mechanics#other-types-of-market-data "Direct link to Other types of market data")

Candlestick charts are built by aggregation of initially limited market data of last trades only (Times & Sales) which consist around 5% of the market data (or information).

What Are the Key Principles of Market Mechanics in Trading?[​](/knowledgebase/docs/KB-Bookmap-Wiki-Market-Mechanics#what-are-the-key-principles-of-market-mechanics-in-trading "Direct link to What Are the Key Principles of Market Mechanics in Trading?")
------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

The core principles are:

1. Orders are the foundation of all price movement.
2. Matching engines apply deterministic rules (FIFO, Pro-Rata, etc.).
3. Market data reflects every trader action in real time.
4. Latency and speed shape who captures opportunities first.

### Comparison of quality of market data sources[​](/knowledgebase/docs/KB-Bookmap-Wiki-Market-Mechanics#comparison-of-quality-of-market-data-sources "Direct link to Comparison of quality of market data sources")

Did you know? Bookmap allows users themselves to compare market data of 2 or more different data vendors. The time range can be either hours or milliseconds. Here is an example: [[3]](https://www.bookmap.com/forum/viewtopic.php?f=12&t=4)

Commissions[​](/knowledgebase/docs/KB-Bookmap-Wiki-Market-Mechanics#commissions "Direct link to Commissions")
-------------------------------------------------------------------------------------------------------------

Commissions that exchanges charge for matching and execution between orders are the main source of their income. They aim to select a matching algorithm that attracts more traders and increases the liquidity of a particular market or asset.

### Market maker vs Market taker[​](/knowledgebase/docs/KB-Bookmap-Wiki-Market-Mechanics#market-maker-vs-market-taker "Direct link to Market maker vs Market taker")

Each trade always occurs between two orders from opposite sides: Buy and Sell. one of the orders must always be a resting limit order while another is the newly arrived order, sometimes called aggressive order. The aggressive order is also called Market Taker while the resting order is called Market Maker, hence the name of a corresponding trading strategy called Market Making [[4]](https://www.youtube.com/watch?time_continue=22&v=WFsvY_YRhvg).

In order to increase liquidity and attract more traders, exchanges may define various commissions structures such as lower (up to negative) commissions for the market makers, and higher commissions for the market takers. Both matching algorithm and commissions structure affect the trading strategy of traders and thus the behavior of a particular market. For instance, the commissions for XBTUSD at BitMEX is -0.0250% (negative) for the market maker and 0.0750% for the market taker, which is ~5 points of its price 6735. To execute an order as a market taker, the trader needs to anticipate price movement of at least 5 points. As a result, it's noticeable that price typically moves in steps of 5 points or more:

![screenshot](/knowledgebase/assets/images/006_Commissions_impact_01-5e6198547aee93c1ac17f7bfcd5775a2.png "Commisions")

Here is such a move in a higher resolution. The intensive attempts of traders to execute their orders as market makers and receive commissions instead of paying them are also noticeable.

![screenshot](/knowledgebase/assets/images/007_Commissions_impact_02-58a191a1a38316ff369172915a7674d5.png "Commisions")

Matching Algorithms[​](/knowledgebase/docs/KB-Bookmap-Wiki-Market-Mechanics#matching-algorithms "Direct link to Matching Algorithms")
-------------------------------------------------------------------------------------------------------------------------------------

The exact algorithm of processing new actions of traders is defined by the Matching Algorithm which is a part of instrument/asset specification. There is a variety of matching algorithms, even within the same exchange. For instance, here is an overview of [CME matching algorithms](https://www.cmegroup.com/education/matching-algorithm-overview.html), followed by their detailed description. The most popular matching algorithm is FIFO, described in detail below. The next most popular matching algorithm is Pro-Rata, which matches orders according to their size and thus allows execution of orders at the end of the queue as well. In general, exchanges select the matching algorithm which satisfies best the traders of a particular market, thus increasing the liquidity of that product and traded volume, and thus the income from commissions.

### Standard Matching Algorithm: Price-Time priority[​](/knowledgebase/docs/KB-Bookmap-Wiki-Market-Mechanics#standard-matching-algorithm-price-time-priority "Direct link to Standard Matching Algorithm: Price-Time priority")

Price-Time priority (aka FIFO: First-in-First-out) is probably the most widely used matching algorithm, for instance, it is used by CME for E-mini S&P 500 (ES) futures.

![screenshot](/knowledgebase/assets/images/008_Standard_Matching_Algorithm-43aa5188ca1b055d5f9d71452db35b38.png "Matching")

Here is an illustration of this process:

![screenshot](/knowledgebase/assets/images/009_Matching_Algorithm_FIFO_with_SRC-602946731ddf020c35d719db2e867a42.png "Matching")

Latency[​](/knowledgebase/docs/KB-Bookmap-Wiki-Market-Mechanics#latency "Direct link to Latency")
-------------------------------------------------------------------------------------------------

As shown on the top diagram, latency comprises of three components:

* The speed of receiving market data
* The speed of processing market data taking into account trader's own status
* Round-trip-time (RTT) is the time period from sending an order (or cancellation or modification) until receiving corresponding feedback from the exchange. It comprises two ways latency and exchange processing time. Traders typically need to get a status update about their previous action before conducting a new one. Otherwise, they may encounter the risk of higher than desired exposure.

### Why low latency is important[​](/knowledgebase/docs/KB-Bookmap-Wiki-Market-Mechanics#why-low-latency-is-important "Direct link to Why low latency is important")

Traders aim to get the advantage of short-term trading opportunities such as arbitrage between correlated and dependent on each other markets, fundamental factors, the behavior of other traders, and so on. There is a large number of trading styles and motivations, well covered and structured by a zero-sum article from 1993 [[5]](http://turtletrader.com/zerosum.pdf) (see tables at the end). Low latency allows getting the advantage of short-term trading opportunities earlier than other traders who noticed the same opportunity. If executed earlier, the other traders will move the price in the desired direction by their actions but may have worse execution prices, and vice versa [[6]](https://bookmap.com/zero-sum-game-principle/).

### Atomic Processing Of Orders[​](/knowledgebase/docs/KB-Bookmap-Wiki-Market-Mechanics#atomic-processing-of-orders "Direct link to Atomic Processing Of Orders")

![screenshot](/knowledgebase/assets/images/010_Latency_Speed_Bumps-8851ee3ce0e9e753d6f2b62b0106ce27.png "Latency")

Traders send their actions asynchronously and may have different latency to the exchange due to geographical location or different infrastructure. These actions must be synchronized at the exchange because different orders of processing of any two actions may lead to different results as shown in this simple example. Typically actions are synchronized according to the order of their arrival (even if two actions arrive at the same nanosecond, there is still the first one). In practice, exchanges may use a smarter approach, allowing to process actions in parallel (e.g. two orders being canceled), but only if the result is the same as if they were processed in an atomic manner. As shown in the Latency section, exchanges may use artificial speed bumps and offer a highway for preferred market participants such as registered market makers. Still, there is an atomic synchronization that takes place at some level before Matching Engine, but it is done by a different logic.

Case Study: Artificial 'Speed Bumps'[​](/knowledgebase/docs/KB-Bookmap-Wiki-Market-Mechanics#case-study-artificial-speed-bumps "Direct link to Case Study: Artificial 'Speed Bumps'")
-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

![screenshot](/knowledgebase/assets/images/011_Speed_Bump_SEC_Approval-b9cd84ff4adc00f4716b40378740d050.png "Speed Bump")

**Chicago Stock Exchange (CHX)** was the first to propose artificial Speed Bumps which should artificially delay incoming traders' actions by 350 microseconds except for the actions of particular market makers who are allowed to use the highway. At first, it was rejected as being discriminatory and because technically it can lead to the following situation: ...concern is that a delayed message might well be delayed for 351 microseconds, 500 microseconds, thousands of microseconds, or even until next Tuesday while the participant submitting that message waits for its message's disposition [[7]](https://www.sec.gov/comments/sr-chx-2017-04/chx201704-1808131-153815.pdf). But later the proposal was approved not only for CHX but also for NYSE [[8]](https://www.sec.gov/rules/sro/nysemkt/2017/34-80700.pdf) and other stock exchanges including not only incoming messages but also outgoing messages. One of the arguments for the approval was that exchanges already give an advantage for registered market makers in various forms including, for instance, determining the position on the orders queue based on FIFO with LMM Matching Algorithm which is an enhanced FIFO algorithm that allows for LMM allocations prior to the FIFO allocations [[9]](https://www.cmegroup.com/confluence/display/EPICSANDBOX/Matching+Algorithms). Artificial speed bumps in effect provide a very similar advantage for preferred by the exchange market participants.

This study case alone demonstrates the importance of latency and the importance of knowing the rules of the game prior to participating in it.

### Latency vs decision quality[​](/knowledgebase/docs/KB-Bookmap-Wiki-Market-Mechanics#latency-vs-decision-quality "Direct link to Latency vs decision quality")

**Low latency** amplifies both good and bad decisions, leading to better or worse results accordingly. For instance, fast execution of a bad prediction of price direction leads to a worse execution price than slower execution of the same decision.

Some trading opportunities are very obvious. For instance, when a sharp move occurs at one of two highly correlative markets when this information reaches traders, it almost certainly will affect their decisions about the other market and thus affect its price. In such scenarios, speed is the crucial (and sometimes the only) component of successful arbitrage.

Market Mechanics Trading for Specific Markets[​](/knowledgebase/docs/KB-Bookmap-Wiki-Market-Mechanics#market-mechanics-trading-for-specific-markets "Direct link to Market Mechanics Trading for Specific Markets")
-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

Market Mechanics Trading for Day Traders[​](/knowledgebase/docs/KB-Bookmap-Wiki-Market-Mechanics#market-mechanics-trading-for-day-traders "Direct link to Market Mechanics Trading for Day Traders")
----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

Day traders can use microstructure to time entries and exits with precision, especially during volatile events. Watching how aggressive orders consume liquidity offers clues about short-term direction.

### Most typical mistakes in Quantitative analysis in trading[​](/knowledgebase/docs/KB-Bookmap-Wiki-Market-Mechanics#most-typical-mistakes-in-quantitative-analysis-in-trading "Direct link to Most typical mistakes in Quantitative analysis in trading")

There is a number of counter-intuitive mistakes that can be made during the development and operation of an automated trading strategy. Here are just two of them, both are related to wrong assumptions about historical data during the development of a strategy. The only 'treatment' in both cases is real trading or trading in an equally competitive and interactive environment.

### Algorithmic Trading with Market Mechanics[​](/knowledgebase/docs/KB-Bookmap-Wiki-Market-Mechanics#algorithmic-trading-with-market-mechanics "Direct link to Algorithmic Trading with Market Mechanics")

Algorithmic systems rely heavily on mechanics: queue position, latency management, and liquidity detection. Many algos are built to exploit these micro advantages systematically.

#### Emulation of latency[​](/knowledgebase/docs/KB-Bookmap-Wiki-Market-Mechanics#emulation-of-latency "Direct link to Emulation of latency")

Here the mistake is an assumption of a constant uniform latency. In fact, the latency (RTT or especially latency of market data) has typically very fat-tailed distribution. For instance, the difference between exchange timestamps and timestamps measured by a co-located server is maybe 1 millisecond on average while only 0.01% of data updates have latency above 100 milliseconds. It would be a mistake to ignore these outliers in simulations. But it would be an almost identically bad mistake to assume that these outliers appear randomly by, for instance, using the historical fat-tailed distribution of latency and generating it randomly in simulations. These outliers are highly correlated with bursts of activity on the market and because the matching engine becomes overloaded. In other words, latency has a conditional distribution depending on bursts of activity in the market, which are typically hard to predict in advance. These bursts of activity indicate that many data-driven trading strategies simultaneously spot the same trading opportunity (or rush to cancel their orders), which means this market situation is pretty obvious to many of them. It's therefore expected for a reasonable pattern detection AI/ML algorithm to find the same opportunities in the historical data. Moreover, given a trade-off, it will sacrifice less obvious but potentially real patterns in favor of obvious but illusionary patterns. If during simulation it assumes the average latency, e.g. 1 ms, it will obviously demonstrate great results, which is an illusion. On the other hand, assuming much higher latency, e.g. 100 ms would significantly distort the simulation because the actual average latency is 1 ms. Also, there are always even farther outliers, e.g. 500 ms latency that occurs in 0.0001% of the data.

This problem is equally relevant for much lower frequency trading strategies including those that use daily data samples, e.g daily candlesticks.

#### Emulation of Own Impact[​](/knowledgebase/docs/KB-Bookmap-Wiki-Market-Mechanics#emulation-of-own-impact "Direct link to Emulation of Own Impact")

![screenshot](/knowledgebase/assets/images/012_Chaotic_systems-c4d46e6a48627fde1f9f9a3ad2b77d9d.gif "Chaotic Systems")

Here the mistake is an assumption of negligible impact of simulated on historical data strategy on market data and on other market participants. The market data wouldn't be the same because trading actions that don't affect the market simply don't exist. The only question is how much would it change the market. Because trading is an interactive process, even relatively small additional activities would impact the data and also trigger different reactions of other market participants, creating a cumulative effect much stronger than added activity. Such cumulative effect of tiny actions is similar to the behavior of a chaotic system, i.e. where infinitesimal differences in the starting conditions lead to drastically different results as the system evolves as shown in this animation.

### Timestamps in Bookmap[​](/knowledgebase/docs/KB-Bookmap-Wiki-Market-Mechanics#timestamps-in-bookmap "Direct link to Timestamps in Bookmap")

**Bookmap allows to zoom-in to nanoseconds,** which is the resolution of its timestamps. This obviously isn't necessary for a chart trader. But whether you use milliseconds, microseconds, or nanoseconds, such timestamp requires a 64-bit Integer. Even seconds timestamp will require 64-bit in several years from now. So, there is no disadvantage of using nanoseconds timestamps in the application. The advantage however is that it is useful for HFT firms who use [the Bookmap Quant solution](https://bookmap.com/knowledgebase/docs/API#the-quant-solution) to visualize data with timestamps recorded at exchange co-located servers where some firms may use GPS clock with 100 nanoseconds precision.

**By default, Bookmap displays timestamps of receiving the data and orders updates on the client-side,** using its computer clock. This is useful for traders regardless of their latency to the exchange because it shows where they could potentially act and where they actually acted. It takes into account potential packet loss during transmission or short-term disconnections, which also allows traders to be alerted in such cases. Displaying exchange timestamps during such cases or within high or non-uniform latency, in general, would mean changing the history from a trader perspective. This would not explain to the trader high slippage during correct decisions. Also, displaying the chart with data receiving timestamps guarantees that market data is stored in chronological order when connecting to low-quality data vendors who may, for instance, provide trades, BBO, and market depth asynchronously.

### Implementations[​](/knowledgebase/docs/KB-Bookmap-Wiki-Market-Mechanics#implementations "Direct link to Implementations")

It's easy to imagine that ancient traders were interested in faster ships and horses to reduce the latency. Today commercial firms invest hundreds of millions USD in layering cross-Atlantic cables under the ocean, reducing the latency by a number of milliseconds and being almost solely purposed for (and afforded by) HFT firms. Another direction being developed and already offered is radio communication, which allows communication almost at the speed of light 0.99c while cable communication speed is ~0.8c. It's possible that HFT firms in the future may use neutrino-based communication because neutrinos can travel at the speed of light 1c through the Earth's core instead of traveling around the Earth like radio waves do [[10]](https://en.wikipedia.org/wiki/MINER%CE%BDA).

Market Mechanics FAQ[​](/knowledgebase/docs/KB-Bookmap-Wiki-Market-Mechanics#market-mechanics-faq "Direct link to Market Mechanics FAQ")
----------------------------------------------------------------------------------------------------------------------------------------

### Are you looking for a specific market to trade?[​](/knowledgebase/docs/KB-Bookmap-Wiki-Market-Mechanics#are-you-looking-for-a-specific-market-to-trade "Direct link to Are you looking for a specific market to trade?")

Market mechanics apply to futures, stocks, and crypto. The principles are the same, though each market has different rules and venues.

### Are you a beginner or an experienced trader?[​](/knowledgebase/docs/KB-Bookmap-Wiki-Market-Mechanics#are-you-a-beginner-or-an-experienced-trader "Direct link to Are you a beginner or an experienced trader?")

Beginners can start by learning order types and how exchanges process them. Experienced traders often dive deeper into latency, matching algorithms, and fee structures.

### Are you interested in a specific indicator for this strategy?[​](/knowledgebase/docs/KB-Bookmap-Wiki-Market-Mechanics#are-you-interested-in-a-specific-indicator-for-this-strategy "Direct link to Are you interested in a specific indicator for this strategy?")

Bookmap offers tools like the Stops & Icebergs indicator and full depth heatmap, which translate market mechanics into clear visuals for traders.

### Market Dynamics Trading Strategy[​](/knowledgebase/docs/KB-Bookmap-Wiki-Market-Mechanics#market-dynamics-trading-strategy "Direct link to Market Dynamics Trading Strategy")

Market dynamics describe how orders, liquidity, and trader behavior interact. A trading strategy based on these dynamics blends market structure analysis with order flow, helping traders understand not just where price is, but why it is moving.

Useful links[​](/knowledgebase/docs/KB-Bookmap-Wiki-Market-Mechanics#useful-links "Direct link to Useful links")
----------------------------------------------------------------------------------------------------------------

--- [Iceberg Orders Tracker](https://bookmap.com/knowledgebase/docs/KB-Bookmap-Wiki-Iceberg-Orders-Tracker)

--- [Market Makers as a news feed](https://twitter.com/bookmap_pro/status/991806902324662272)

--- [CME matching algorithms](https://www.cmegroup.com/education/matching-algorithm-overview.html)

--- [How to compare the data from different market data vendors](https://www.bookmap.com/forum/viewtopic.php?f=12&t=4)

--- [Practical use of Zero-Sum-Game principle in trading](https://bookmap.com/zero-sum-game-principle/)

--- [Styles and Motivations of traders and relationship between them](http://turtletrader.com/zerosum.pdf)

--- [What Is Market Making?](https://www.youtube.com/watch?time_continue=22&v=WFsvY_YRhvg)

--- [Prediction quality by betting systems](https://www.youtube.com/watch?v=Qjx9WO_YTyU)

[Previous
Iceberg Orders Tracker](/knowledgebase/docs/KB-Bookmap-Wiki-Iceberg-Orders-Tracker)[Next
Bookmap Quant Solution: Setup and Features](/knowledgebase/docs/KB-AdvancedSolution-Bookmap-Quant-Solution-Setup)

* [Why should I read it?](/knowledgebase/docs/KB-Bookmap-Wiki-Market-Mechanics#why-should-i-read-it)
* [Market Mechanics Trading Approach](/knowledgebase/docs/KB-Bookmap-Wiki-Market-Mechanics#market-mechanics-trading-approach)
* [Trading Strategy Based on Market Mechanics](/knowledgebase/docs/KB-Bookmap-Wiki-Market-Mechanics#trading-strategy-based-on-market-mechanics)
+ [Wars do not affect the market](/knowledgebase/docs/KB-Bookmap-Wiki-Market-Mechanics#wars-do-not-affect-the-market)
+ [There are no 'macro' events in the market](/knowledgebase/docs/KB-Bookmap-Wiki-Market-Mechanics#there-are-no-macro-events-in-the-market)
+ [Put your money where your mouth is](/knowledgebase/docs/KB-Bookmap-Wiki-Market-Mechanics#put-your-money-where-your-mouth-is)
+ [Know the rules of the game](/knowledgebase/docs/KB-Bookmap-Wiki-Market-Mechanics#know-the-rules-of-the-game)
* [How to Trade Using Market Mechanics](/knowledgebase/docs/KB-Bookmap-Wiki-Market-Mechanics#how-to-trade-using-market-mechanics)
* [Factors for success in trading](/knowledgebase/docs/KB-Bookmap-Wiki-Market-Mechanics#factors-for-success-in-trading)
* [How to Analyze Market Mechanics](/knowledgebase/docs/KB-Bookmap-Wiki-Market-Mechanics#how-to-analyze-market-mechanics)
* [Orders](/knowledgebase/docs/KB-Bookmap-Wiki-Market-Mechanics#orders)
+ [Examples of Market Mechanics Trading Strategies](/knowledgebase/docs/KB-Bookmap-Wiki-Market-Mechanics#examples-of-market-mechanics-trading-strategies)
+ [Actions of traders](/knowledgebase/docs/KB-Bookmap-Wiki-Market-Mechanics#actions-of-traders)
* [Order Book](/knowledgebase/docs/KB-Bookmap-Wiki-Market-Mechanics#order-book)
* [Market Data types](/knowledgebase/docs/KB-Bookmap-Wiki-Market-Mechanics#market-data-types)
+ [Market by Price](/knowledgebase/docs/KB-Bookmap-Wiki-Market-Mechanics#market-by-price)
+ [Market by Order](/knowledgebase/docs/KB-Bookmap-Wiki-Market-Mechanics#market-by-order)
+ [Other types of market data](/knowledgebase/docs/KB-Bookmap-Wiki-Market-Mechanics#other-types-of-market-data)
* [What Are the Key Principles of Market Mechanics in Trading?](/knowledgebase/docs/KB-Bookmap-Wiki-Market-Mechanics#what-are-the-key-principles-of-market-mechanics-in-trading)
+ [Comparison of quality of market data sources](/knowledgebase/docs/KB-Bookmap-Wiki-Market-Mechanics#comparison-of-quality-of-market-data-sources)
* [Commissions](/knowledgebase/docs/KB-Bookmap-Wiki-Market-Mechanics#commissions)
+ [Market maker vs Market taker](/knowledgebase/docs/KB-Bookmap-Wiki-Market-Mechanics#market-maker-vs-market-taker)
* [Matching Algorithms](/knowledgebase/docs/KB-Bookmap-Wiki-Market-Mechanics#matching-algorithms)
+ [Standard Matching Algorithm: Price-Time priority](/knowledgebase/docs/KB-Bookmap-Wiki-Market-Mechanics#standard-matching-algorithm-price-time-priority)
* [Latency](/knowledgebase/docs/KB-Bookmap-Wiki-Market-Mechanics#latency)
+ [Why low latency is important](/knowledgebase/docs/KB-Bookmap-Wiki-Market-Mechanics#why-low-latency-is-important)
+ [Atomic Processing Of Orders](/knowledgebase/docs/KB-Bookmap-Wiki-Market-Mechanics#atomic-processing-of-orders)
* [Case Study: Artificial 'Speed Bumps'](/knowledgebase/docs/KB-Bookmap-Wiki-Market-Mechanics#case-study-artificial-speed-bumps)
+ [Latency vs decision quality](/knowledgebase/docs/KB-Bookmap-Wiki-Market-Mechanics#latency-vs-decision-quality)
* [Market Mechanics Trading for Specific Markets](/knowledgebase/docs/KB-Bookmap-Wiki-Market-Mechanics#market-mechanics-trading-for-specific-markets)
* [Market Mechanics Trading for Day Traders](/knowledgebase/docs/KB-Bookmap-Wiki-Market-Mechanics#market-mechanics-trading-for-day-traders)
+ [Most typical mistakes in Quantitative analysis in trading](/knowledgebase/docs/KB-Bookmap-Wiki-Market-Mechanics#most-typical-mistakes-in-quantitative-analysis-in-trading)
+ [Algorithmic Trading with Market Mechanics](/knowledgebase/docs/KB-Bookmap-Wiki-Market-Mechanics#algorithmic-trading-with-market-mechanics)
+ [Timestamps in Bookmap](/knowledgebase/docs/KB-Bookmap-Wiki-Market-Mechanics#timestamps-in-bookmap)
+ [Implementations](/knowledgebase/docs/KB-Bookmap-Wiki-Market-Mechanics#implementations)
* [Market Mechanics FAQ](/knowledgebase/docs/KB-Bookmap-Wiki-Market-Mechanics#market-mechanics-faq)
+ [Are you looking for a specific market to trade?](/knowledgebase/docs/KB-Bookmap-Wiki-Market-Mechanics#are-you-looking-for-a-specific-market-to-trade)
+ [Are you a beginner or an experienced trader?](/knowledgebase/docs/KB-Bookmap-Wiki-Market-Mechanics#are-you-a-beginner-or-an-experienced-trader)
+ [Are you interested in a specific indicator for this strategy?](/knowledgebase/docs/KB-Bookmap-Wiki-Market-Mechanics#are-you-interested-in-a-specific-indicator-for-this-strategy)
+ [Market Dynamics Trading Strategy](/knowledgebase/docs/KB-Bookmap-Wiki-Market-Mechanics#market-dynamics-trading-strategy)
* [Useful links](/knowledgebase/docs/KB-Bookmap-Wiki-Market-Mechanics#useful-links)






![](https://www.facebook.com/tr?id=2704626723097521&ev=PageView&noscript=1)

![](https://t.co/1/i/adsct?bci=4&dv=UTC%26en-US%2Cen%26Google%20Inc.%26Linux%20x86_64%26255%26800%26600%264%2624%26800%26600%260%26na&eci=3&email_address=74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b&event=%7B%7D&event_id=63192bf9-b472-44bd-8905-b39e6a45ba53&integration=gtm&p_id=Twitter&p_user_id=0&pl_id=0700f068-0f6a-46bd-b56a-3eccf3dbfb4c&pt=Market%20Mechanics%20%7C%20Bookmap%20Knowledge%20Base&tw_document_href=https%3A%2F%2Fbookmap.com%2Fknowledgebase%2Fdocs%2FKB-Bookmap-Wiki-Market-Mechanics&tw_iframe_status=0&txn_id=ofl3h&type=javascript&version=2.3.34)![](https://analytics.twitter.com/1/i/adsct?bci=4&dv=UTC%26en-US%2Cen%26Google%20Inc.%26Linux%20x86_64%26255%26800%26600%264%2624%26800%26600%260%26na&eci=3&email_address=74234e98afe7498fb5daf1f36ac2d78acc339464f950703b8c019892f982b90b&event=%7B%7D&event_id=63192bf9-b472-44bd-8905-b39e6a45ba53&integration=gtm&p_id=Twitter&p_user_id=0&pl_id=0700f068-0f6a-46bd-b56a-3eccf3dbfb4c&pt=Market%20Mechanics%20%7C%20Bookmap%20Knowledge%20Base&tw_document_href=https%3A%2F%2Fbookmap.com%2Fknowledgebase%2Fdocs%2FKB-Bookmap-Wiki-Market-Mechanics&tw_iframe_status=0&txn_id=ofl3h&type=javascript&version=2.3.34)



