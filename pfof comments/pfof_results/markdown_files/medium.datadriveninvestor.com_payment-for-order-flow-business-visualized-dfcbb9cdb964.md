---
                title: "('Payment For Order Flow Business Visualized',)"
                url: "https://medium.datadriveninvestor.com/payment-for-order-flow-business-visualized-dfcbb9cdb964"
                date: "5/24/21"
                sentiment: "('Neutral',)"
                topic: "pfof"
                ---

                
[Sitemap](/sitemap/sitemap.xml)
[Open in app](https://rsci.app.link/?%24canonical_url=https%3A%2F%2Fmedium.com%2Fp%2Fdfcbb9cdb964&%7Efeature=LoOpenInAppButton&%7Echannel=ShowPostUnderCollection&%7Estage=mobileNavBar&source=post_page---top_nav_layout_nav-----------------------------------------)

Sign up

[Sign in](https://medium.com/m/signin?operation=login&redirect=https%3A%2F%2Fmedium.datadriveninvestor.com%2Fpayment-for-order-flow-business-visualized-dfcbb9cdb964&source=post_page---top_nav_layout_nav-----------------------global_nav------------------)




[Medium Logo](https://medium.com/?source=post_page---top_nav_layout_nav-----------------------------------------)





[Write](https://medium.com/m/signin?operation=register&redirect=https%3A%2F%2Fmedium.com%2Fnew-story&source=---top_nav_layout_nav-----------------------new_post_topnav------------------)
[Search](https://medium.com/search?source=post_page---top_nav_layout_nav-----------------------------------------)

Sign up

[Sign in](https://medium.com/m/signin?operation=login&redirect=https%3A%2F%2Fmedium.datadriveninvestor.com%2Fpayment-for-order-flow-business-visualized-dfcbb9cdb964&source=post_page---top_nav_layout_nav-----------------------global_nav------------------)



![](https://miro.medium.com/v2/resize:fill:64:64/1*dmbNkD5D-u45r44go_cf0g.png)



[DataDrivenInvestor
------------------](https://medium.datadriveninvestor.com/?source=post_page---publication_nav-32881626c9c9-dfcbb9cdb964---------------------------------------)
·

Follow publication




[![DataDrivenInvestor](https://miro.medium.com/v2/resize:fill:76:76/1*2mBCfRUpdSYRuf9EKnhTDQ.png)](https://medium.datadriveninvestor.com/?source=post_page---post_publication_sidebar-32881626c9c9-dfcbb9cdb964---------------------------------------)

empowerment through data, knowledge, and expertise. Join DDI community at <https://join.datadriveninvestor.com>

Follow publication


Payment For Order Flow Business Visualized
==========================================

[![Diego Alvarez](https://miro.medium.com/v2/resize:fill:64:64/1*0QSMr3Yv8rxZAHxxQC5pNQ.jpeg)](https://dial0663.medium.com/?source=post_page---byline--dfcbb9cdb964---------------------------------------)
[Diego Alvarez](https://dial0663.medium.com/?source=post_page---byline--dfcbb9cdb964---------------------------------------)



6 min read·
Apr 1, 2021


--





Listen


Share






Press enter or click to view image in full size![]()

Order flow example with payment for order flow (PFOF)

Payment for order flow has gone from a term that was glossed over in a standard user agreements to the most debated topic in retail trading. There are a lot of misconceptions about how this transaction works, and the topic is quite polarizing depending on your perspective. This article will try to provide the market of payment for order flow transaction with as little bias as possible. There are ultimately benefits and drawbacks for implementing payment for order flow.

This article also generalizes aspects of market-making and market microstructure, the processes behind these transactions are much more complex then how they are presented in this article.

To summarize the whole business, payment for order flow is essentially paying to do latency arbitrage. Financial terms are aptly named, therefore arbitrage which is when one security is quoted at different prices, and latency is a computer-science term for lag. Latency arbitrage is taking advantage of lags within the market. In this case the mispricing comes from market participants offering to buy and sell the same security at different prices.

Within this article we will be using 3 parties: the buyer, the broker, and the high frequency trader (HFT) / market-maker (MM). In this case our example will be a customer submitting a buy order for a single stock. The business is similar for other securities as well, but a bit more complicated.

Before we jump into the framework its noteworthy to discuss why its been in the news so much. The business has been under regulatory scrutiny for its alleged role in GameStop-related short squeeze. Although the CEO of Robinhood said that the trading activity during the short-squeeze was related to a collateral call that the brokerage couldn’t make from their clearinghouse, high frequency traders (HFTs) were brought into the mix.

Let’s begin by looking at a customer who is looking to submit an order to buy a single share of stock. The process may look something like this.

Press enter or click to view image in full size![]()

Now we have to introduce slippage. Slippage is the money lost during trading, because the market moves in the opposite direction to the trade. Within a trading strategy, slippage is going to exist when using market orders. In this case with a buy order slippage would occur when you submit a buy order but the stock price goes down during the time it takes to execute the trade. This is because there is some latency between submitting the order to the exchange and getting filled. During that time the price is being updated and it in this case it moves against the order. Let’s say that the stock the buyer is interested in trades at $100. Slippage would look something like this.

Press enter or click to view image in full size![]()

For the most part every trader will have slippage, the only way to negate slippage is reduce the latency between the computer used for submitting the order and the exchange. That’s a whole business within itself where HFTs reduce latency via colocation and other hardware / software solutions. Also in real life scenarios slippage is probably not as big as the example for most liquid stocks.

HFTs are market makers which mean their jobs is to facilitate transactions. Essentially latency based arbitrage is when the HFT trader arbitrages between the market price and the incoming orders. They can do this because they have a faster connection to the exchanges. The process of a high frequency trader making a market for that $100 buy order would look something like this.

Press enter or click to view image in full size![]()

There are a couple of things worth mentioning when looking at this diagram. The first is that the money that the HFT makes is not always $1, it is probably much smaller. (The FCA estimates its around 0.0042% of liquid stocks see [link](https://www.wsj.com/articles/ultrafast-trading-costs-stock-investors-nearly-5-billion-a-year-study-says-11580126036#:~:text=High%2Dfrequency%20traders%20earn%20nearly,investors%2C%20a%20new%20study%20says.)). Also the placement of the HFT makes it look like it can see ahead in the future, really that is to show that the HFT has a faster connectivity.

Now comes payment for order flow. Essentially what happens is that the HFT pays the broker to get a first look at the trade before it hits the exchange. The order flow would look like this.

Press enter or click to view image in full size![]()

Something to acknowledge is that when the order is put onto the exchange there will also be slippage as well.

Something to note is that volatility plays a huge role in market making. Volatility is the measurement for how big the price movements are. More volatile stocks are going to have bigger prices movements. So stocks with greater volatility will vary greater and which means that the HFT will find a bigger spread. An example of a more volatile stock may look like.

Press enter or click to view image in full size![]()

Below is as link to an article from the WSJ that backs this claim up. They agree that high volatility which means the price swings move at a greater magnitude give HFT traders bigger profit.

[![]()](https://www.wsj.com/articles/high-frequency-traders-feast-on-volatile-market-11585310401#:~:text=High%2Dfrequency%20traders%2C%20which%20typically,well%20when%20markets%20are%20volatile.)

WSJ on volatility and High Frequency Trading.

Without the stock prices or timeline the order flow would look like this.

Press enter or click to view image in full size![]()

So where does the payment come in, and why would a HFT pay? The HFT pays the brokerage because it gives them a “look-ahead” on the order. From the HFT’s perspective its more cost-effective to pay the broker for the order flow than to find the order on the exchange and compete with other HFTs. The broker uses payment for order flow because they can offer commission-free trading. And the customer uses it because they can trade without commissions. Tracking the payments in payments looks like.

![]()

Essentially commission-free trading exists because of payment for order flow, without that brokers would have to roll over the commission costs to the customer.

There is a reason why HFTs target retail traders rather than institutional traders. Its because retail traders are less likely to leave a trade than institutional investors with HFT. In economics terms the marginal cost of trading is greater for institutional traders than for retail traders. In more simpler terms, if a HFT makes 0.01% on trades an institutional trader trading $1bn would take a bigger hit than a retail trader with $100. From a mathematical-like approach HFTs think like this.

![]()

At the moment the HFT and Payment for order flow business is relatively strong. Recent reports show that HFT Market Makers such as Virtu, Citadel Securities, and Susquehanna paid around $2.9bn for order flow in 2020 according to Bloomberg data (read article [here](https://www.ft.com/content/b1798a5f-2529-4d6f-a11b-08a5aa99fe63)). There is fair criticism on both sides and claims that have yet to be substantiated and are still debated to this day.

You can read more about high frequency trading and its praises and criticisms here.

<https://www.bloomberg.com/quicktake/payment-for-order-flow>

[Virtu boss defends payment for order flow after Reddit frenzy
-------------------------------------------------------------

### Virtu Financial, one of the world's largest market makers, has defended the practice of paying retail brokers to take…


www.ft.com](https://www.ft.com/content/b1798a5f-2529-4d6f-a11b-08a5aa99fe63?source=post_page-----dfcbb9cdb964---------------------------------------)
[GameStop, Payments for Order Flow, and High Frequency Trading
-------------------------------------------------------------

### The trading platform Robinhood, used by many small investors who recently purchased GameStop stock, funds itself…


www.cato.org](https://www.cato.org/blog/gamestop-payments-order-flow-high-frequency-trading?source=post_page-----dfcbb9cdb964---------------------------------------)

You can find me on my [**LinkedIn**](https://www.linkedin.com/in/diegodalvarez/) and [**GitHub**](https://github.com/diegodalvarez)

[How Finance Sector Can Benefit by Machine Learning Development and AI | DataDrivenInvestor
------------------------------------------------------------------------------------------

### Making the right decisions and grabbing opportunities in the fast moving world of finance can make a difference to your…


www.datadriveninvestor.com](https://www.datadriveninvestor.com/2020/07/28/how-finance-sector-can-benefit-by-machine-learning-development-and-ai/?source=post_page-----dfcbb9cdb964---------------------------------------)

**Gain Access to Expert View —** [**Subscribe to DDI Intel**](https://www.datadriveninvestor.com/ddintel-subscription/)





[Finance](https://medium.com/tag/finance?source=post_page-----dfcbb9cdb964---------------------------------------)
[Trading](https://medium.com/tag/trading?source=post_page-----dfcbb9cdb964---------------------------------------)
[High Frequency Trading](https://medium.com/tag/high-frequency-trading?source=post_page-----dfcbb9cdb964---------------------------------------)
[Finance And Banking](https://medium.com/tag/finance-and-banking?source=post_page-----dfcbb9cdb964---------------------------------------)


[![DataDrivenInvestor](https://miro.medium.com/v2/resize:fill:96:96/1*2mBCfRUpdSYRuf9EKnhTDQ.png)](https://medium.datadriveninvestor.com/?source=post_page---post_publication_info--dfcbb9cdb964---------------------------------------)
[![DataDrivenInvestor](https://miro.medium.com/v2/resize:fill:128:128/1*2mBCfRUpdSYRuf9EKnhTDQ.png)](https://medium.datadriveninvestor.com/?source=post_page---post_publication_info--dfcbb9cdb964---------------------------------------)
Follow

[Published in DataDrivenInvestor
-------------------------------](https://medium.datadriveninvestor.com/?source=post_page---post_publication_info--dfcbb9cdb964---------------------------------------)
[103K followers](/followers?source=post_page---post_publication_info--dfcbb9cdb964---------------------------------------)
·[Last published 5 days ago](/the-same-mistake-different-technology-f918a8845798?source=post_page---post_publication_info--dfcbb9cdb964---------------------------------------)


empowerment through data, knowledge, and expertise. Join DDI community at <https://join.datadriveninvestor.com>



Follow

[![Diego Alvarez](https://miro.medium.com/v2/resize:fill:96:96/1*0QSMr3Yv8rxZAHxxQC5pNQ.jpeg)](https://dial0663.medium.com/?source=post_page---post_author_info--dfcbb9cdb964---------------------------------------)
[![Diego Alvarez](https://miro.medium.com/v2/resize:fill:128:128/1*0QSMr3Yv8rxZAHxxQC5pNQ.jpeg)](https://dial0663.medium.com/?source=post_page---post_author_info--dfcbb9cdb964---------------------------------------)


[Written by Diego Alvarez
------------------------](https://dial0663.medium.com/?source=post_page---post_author_info--dfcbb9cdb964---------------------------------------)
[45 followers](https://dial0663.medium.com/followers?source=post_page---post_author_info--dfcbb9cdb964---------------------------------------)
·[446 following](https://medium.com/@dial0663/following?source=post_page---post_author_info--dfcbb9cdb964---------------------------------------)


CU Boulder undergraduate studying math. Interested in machine learning, algorithmic trading, and cyber security. @dial0663






No responses yet
----------------






[Help](https://help.medium.com/hc/en-us?source=post_page-----dfcbb9cdb964---------------------------------------)
[Status](https://status.medium.com/?source=post_page-----dfcbb9cdb964---------------------------------------)
[About](https://medium.com/about?autoplay=1&source=post_page-----dfcbb9cdb964---------------------------------------)
[Careers](https://medium.com/jobs-at-medium/work-at-medium-959d1a85284e?source=post_page-----dfcbb9cdb964---------------------------------------)
[Press](mailto:pressinquiries@medium.com)
[Blog](https://blog.medium.com/?source=post_page-----dfcbb9cdb964---------------------------------------)
[Privacy](https://policy.medium.com/medium-privacy-policy-f03bf92035c9?source=post_page-----dfcbb9cdb964---------------------------------------)
[Rules](https://policy.medium.com/medium-rules-30e5502c4eb4?source=post_page-----dfcbb9cdb964---------------------------------------)
[Terms](https://policy.medium.com/medium-terms-of-service-9db0094a1e0f?source=post_page-----dfcbb9cdb964---------------------------------------)
[Text to speech](https://speechify.com/medium?source=post_page-----dfcbb9cdb964---------------------------------------)









