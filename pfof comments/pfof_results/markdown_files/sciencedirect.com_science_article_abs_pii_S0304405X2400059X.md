---
                title: "('Tiny trades, big questions: Fractional shares',)"
                url: "https://sciencedirect.com/science/article/abs/pii/S0304405X2400059X"
                date: ""
                sentiment: "('Neutral',)"
                topic: "pfof"
                ---

                
JavaScript is disabled on your browser.
Please enable JavaScript to use all the features on this page.
![](https://smetrics.elsevier.com/b/ss/elsevier-sd-prod/1/G.4--NS/1759349391989?pageName=sd%3Aproduct%3Ajournal%3Aarticle&c16=els%3Arp%3Ast&c2=sd&v185=img&v33=ae%3AANON_GUEST&c1=ae%3A228598&c12=ae%3A12975512)

[Skip to main content](#screen-reader-main-content)[Skip to article](#screen-reader-main-title)

* [Access through **your organization**](/user/institution/login?targetUrl=%2Fscience%2Farticle%2Fpii%2FS0304405X2400059X)
* [Purchase PDF](/getaccess/pii/S0304405X2400059X/purchase)

Search ScienceDirect








Article preview
---------------

* [Abstract](#preview-section-abstract)
* [Introduction](#preview-section-introduction)
* [Section snippets](#preview-section-snippets)
* [References (22)](#preview-section-references)
* [Cited by (3)](#preview-section-cited-by)

[![Elsevier](/eu-west-1/prod/778ce9948bc6c58816e88021beca77d5d0d7fce2/image/elsevier-non-solus.svg)](/journal/journal-of-financial-economics "Go to Journal of Financial Economics on ScienceDirect")

[Journal of Financial Economics](/journal/journal-of-financial-economics "Go to Journal of Financial Economics on ScienceDirect")
---------------------------------------------------------------------------------------------------------------------------------

[Volume 157](/journal/journal-of-financial-economics/vol/157/suppl/C "Go to table of contents for this volume/issue"), July 2024, 103836

[![Journal of Financial Economics](https://ars.els-cdn.com/content/image/1-s2.0-S0304405X24X00069-cov150h.gif)](/journal/journal-of-financial-economics/vol/157/suppl/C)

Tiny trades, big questions: Fractional shares
=============================================

Author links open overlay panelRobert P. Bartlett a, Justin McCrary b, Maureen O'Hara c


Show more
Add to MendeleyShare
Cite


[https://doi.org/10.1016/j.jfineco.2024.103836](https://doi.org/10.1016/j.jfineco.2024.103836 "Persistent link using digital object identifier")[Get rights and content](https://s100.copyright.com/AppDispatchServlet?publisherName=ELS&contentID=S0304405X2400059X&orderBeanReset=true)

Abstract
--------

This paper investigates fractional share trading. We develop a latency-based method for identifying a large sample of fractional share trades. We find that high-priced stocks, meme stocks, IPOs, SPACs, and popular retail stocks exhibit considerable numbers of these tiny trades. We surmise that this reflects dollar-based order entry, with many tiny trades being fractional components of larger orders. We show that our fractional trade measure is predictive of future liquidity and volatility, suggesting a new metric to capture the information in retail trades. We identify how data and reporting protocols preclude knowing the extent of fractional share trading, inflate volume data, and provide censured samples of these off-exchange trades.


Introduction
------------

Retail trading in equities markets is enjoying a renaissance. No longer the “quirky side show” of years past, estimates of retail trading rose from 20% of the market in 2010, to perhaps as high as 40% in 2021.1 U.S. retail brokerage accounts increased from 59 million in 2019 to 95 million in 2021. Fidelity alone had 32.5 million accounts in 2021, with Charles Schwab reaching 29.6 million accounts and relatively new entrant Robinhood Markets hitting 23 million accounts and hosting 13 million monthly users.2 Causes of this retail resurgence are varied, but the entrance of fintech trading apps such as Robinhood and Cash-App, the introduction of commission-free trading in 2018, and even the distribution of stimulus checks are noted as prime factors.3 So, too, is the introduction of fractional share trading in 2019 which allowed investors to purchase as little as $1 of high-priced stocks like Berkshire-Hathaway A and Tesla. This paper investigates fractional share trading with a particular focus on understanding both the scale and impact of this new innovation.
Fractional shares are not really new—and they were usually viewed as a problem. Traditionally, fractional shares arose as part of stock dividends that were paid out in shares (or scrips if arising from a stock split), with dividend reinvestment programs (DRIPs) the modern formulation of this practice.4 An article in the New York Times in 1930 decried fractional shares as a “nuisance” which “clutter up” accounts, are expensive to service, and difficult to sell.5 The modern incarnation of fractional share trading is very different in both motivation and practice. In 2019, brokerage firms Interactive Brokers and Robinhood set up dedicated fractional share trading operations to allow retail customers to invest a specific amount of money in a stock rather than buy a specific number of shares. Other major retail brokers quickly followed suit, paving the way for retail access to even the most expensive shares. This dollar-based purchasing also set the stage for individual indexing, whereby retail traders can create personalized indexes largely composed of fractional shares.6

But like in times past, problems remain and even gauging the scale and scope of this fractional development is challenging. Fractional share trades essentially fall outside of the National Market System (NMS). No exchange will accept an order for a fractional share, which means all trading takes place in off-exchange venues. Fractional share trades are not included in the Rule 605 execution quality reports required of market venues, so metrics such as transaction costs are not easily determined. As we detail below, it is not even clear exactly how many fractional share trades occur due to the disparate clearing and reporting protocols that attach to these tiny transactions. Adding to the confusion, the consolidated tape does not accept trade reports for less than a single share so even the fractional share trades that do report “round up” to one share even if the actual trade is for a vastly lower quantity. Bartlett et al. (2022) show how this FINRA (Financial Industry Regulatory Authority) rule resulted in volume on the tape being drastically over-stated for the Class A common stock of Berkshire Hathaway (BRK.A), causing the relationship between BRK.A and its paired stock BRK.B to break down, and introducing a variety of other negative effects for those securities.
In this paper, our interest lies in addressing some “big” questions inherent in fractional share trading. First, how important are fractional share trades and what determines their daily incidence across stocks? Are they only used to access high-priced stocks or are fractional share trades ubiquitous across the market? Second, do these tiny trades actually matter in any meaningful sense for the market? For instance, are they predictive of value-relevant data such as future liquidity and volatility? Can fractional shares provide a useful metric for capturing retail trading? Third, as fractional share trading continues to grow, what challenges does the current reporting regime pose for market structure researchers? In particular, how well do the FINRA weekly OTC Transparency data—which, as we show, is a source for weekly data on fractional share trades—capture fractional share trading? Are there biases in how it is calculated and if so how much do they matter? Does the over-counting of volume in the consolidated tape arising from fractional shares constitute a general problem for the market or is this problem largely confined to a subset of high-priced stocks?
Fundamental to being able to address any of these questions is identifying actual fractional share trades in intra-day data. We do so by using the “digital footprints” of one-share trades reported by the two largest fractional share brokers, Robinhood and Drivewealth (henceforth RHDW trades). Our sample period runs from March 1, 2021 through March 31, 2022, and we use our approach and intra-day data to classify trades as fractional share RHDW trades during this time period. We additionally test our classification model using weekly data from the FINRA OTC Transparency platform, which we show can be used to track a portion of the fractional share trades that occur each week in the market. We demonstrate that during our sample period our classifier performs well in predicting fractional share trades reported in the OTC Transparency data. In the Appendix, we illustrate how to test and validate this approach applied to more recent periods, giving researchers a potential framework for detecting these tiny trades in the intraday trade data.
Our research provides a number of contributions to the literature. First, we provide some of the first evidence on what is fast becoming an important avenue for retail trade. We find, for example, that during our sample period TSLA fractional share executions by Robinhood and Drivewealth accounted for 6.7 % of all TSLA trades, over 25% of all single share trades in the market, and a remarkable 48% of single share trades reported to FINRA. Across the 30 stocks with the most fractional share trades, fractional RHDW trades accounted for between 16% to 40% of all reported single share trades and between 31% and 50% of all reported single share FINRA trades. Across all stocks in our sample, 1.5% of trades are fractional RHDW trades, with 13.2% of all single-share trades being of this form. Our work also demonstrates that fractional shares are not just used to buy tiny pieces of high-priced stocks—of the top 30 stocks with the largest number of RHDW fractional share trades, 30% had closing prices less than $50.00 per share. This breadth is exactly what one would expect in a world where orders are increasingly entered in dollars rather than whole-shares.
Second, we demonstrate that fractional share trades may be for small amounts, but they can nevertheless contain value-relevant information, such as with respect to future volatility and spread movements. Regression estimates indicate that a 10% increase in RHDW fractional share trades is associated with an 8-basis point increase in the following day's Averaged Percentage Effective Spread; this elasticity is even larger if we include only the top 100 fractionally traded stocks. Similar predictability arises with respect to intra-day volatility and implied volatilities. We also show that that this predictive power is beyond what is captured in the widely-used retail trading measure from Boehmer et al. (2021)(BJZZ), a result we believe is most likely due to fractional share trades being the fractional component of a larger retail trade. Our results here show that our metric for identifying RHDW fractional share trades (which we refer to as the RHDW-FT metric) can be a valuable and generally more accurate metric for representing retail trade.
Third, notwithstanding our ability to detect RHDW fractional share trades during our sample period, we establish that there remains a remarkable lack of clarity regarding this growing market. Somewhat surprisingly, the current reporting regime undercounts fractional share *trades* but overcounts fractional share trading *volume*.
With respect to trade counts, due to disparate reporting protocols, there is no way to know the total size of the market. As we discuss, not all brokerage firms report fractional share trades to the tape and, among those that do, our framework is limited to identifying those executed by Robinhood and Drivewealth during our sample period. For other firms, we illustrate how to use the OTC Transparency data to track their fractional share trades on a weekly basis, but these data often undercount such trades due to censoring. We document that these data are not actually that transparent. Indeed, we find that for 64% of the stocks in our sample, the OTC Transparency data does not provide data for Robinhood's fractional share trades for even a single week during our sample period where our classifier estimates Robinhood executed at least 200 fractional share trades for the week. For 90% of stocks in our sample, the OTC Transparency initiative includes data for less than half of these weeks.
With respect to volume distortions, we show that fractional share trades that are reported to the tape inflate reported trading volume. Because each fractional share trade must be rounded up to a whole share when reported to the tape, we estimate that overall trading volume was inflated by roughly $200 billion during our sample period due solely to RHDW fractional share trades. The distortions due to the overcounting of volume are worrisome given the link of volume metrics to legal contexts such as the rules relating to corporate stock repurchases and whether investors can bring a class action fraud lawsuit.
Our research is related to several strands of the literature. There is to date only a small literature looking at fractional share trades. Da et al. (2024) provide an interesting event study of the market impacts when four retail brokerage firms first introduce the ability to trade fractional shares in 2019 and 2020. They find that fractional share trading generates price pressures and reversals for high priced stocks during attention generating events. Our findings on the scale and incidence of fractional share trading suggest that these effects may now be even more broadly found in the market. Bartlett et al. (2022), in a companion paper, show how FINRA reporting rules resulted in severely inflated trading volumes for BRK.A, and affected liquidity and pricing in the market. Our work goes beyond this example to examine the incidence of fractional share trading more broadly and its informational content, while documenting the way that current disclosure rules obfuscate our understanding of this increasingly important form of trading.
There is a much larger literature on retail trading. Relevant for our paper is recent research on Robinhood trading and its impacts. Welch (2021) finds that Robinhood traders generally tilt towards high-volume, high-priced stocks with results suggesting both good timing and good alpha. Barber et al. (2022a) find that Robinhood traders engage in more attention-induced trading than other retail traders. Moss et al. (2023) find that ESG disclosures are irrelevant to Robinhood traders’ portfolio allocation decisions. Notably, all of these papers rely on data provided by Robintrack.net, which was decommissioned in August 2020. Our analysis here provides the first look at the extensive use of fractional share trading by Robinhood traders and during a period of time that is unavailable through Robintrack.net.
A second strand of the literature develops proxies for retail trading. Early attempts [see for example Lee and Radhakrishna (2000)] used small trade size as a proxy for retail orders. The rise of algorithmic trading and other market trends, however, renders such an approach untenable (see O'Hara (2015) or O'Hara and Ye (2014) for discussion). BJZZ propose a metric that uses price improvement measured in small fractions of cents per share to identify retail trades arising from marketable orders, but recent papers [see Barber et al. (2022b); Shearer (2022); and Battalio et al. (2023)] raise concerns as to its accuracy. These authors find Type 1 and Type 2 errors in retail order identification and order signing using the BJZZ metric, which they attribute to the metric missing many retail trades due to its exclusion of mid-point trades and trades at the quotes while also faltering by including as retail trades some trades actually executed by institutional traders. As we show here, also missing from this BJZZ metric is any ability to capture fractional share trades.
Finally, there is a growing literature investigating whether retail trade is predictive of future price movements [see, for example, Barber et al. (2009); Kaniel et al. (2008)]. Jones et al. (2022), using the BJZZ metric to identify retail trading in the pandemic, conclude that such trades are predictive of future stock prices. Given recent criticism of the BJZZ metric, the latency-based digital footprint framework we develop here provides an alternative metric to identify a subset of retail trades during our sample period. Indeed, relative to the BJZZ proxy, we illustrate how fractional share trades represent a “distilled” measure of retail order flow that captures what we refer to as “app-based” trading—that is, retail trading that originates largely from mobile-first trading applications. Consistent with this claim, we find that fractional share trades have much stronger predictability of future liquidity and volatility than the BJZZ metric, which most likely reflects the fact that fractional share trades are often the fractional component of a larger retail order. These findings suggest fractional share trading as captured by our RHDW-FT metric can provide a better proxy for identifying the type of retail order flow likely to be predictive of future movements in liquidity and volatility.
This paper is organized as follows. The next section examines the challenges of finding fractional share trades in the consolidated trading data, setting out the current reporting rules and illustrating why many of these trades are captured in FINRA's weekly OTC Transparency data. We also describe how we exploit existing disclosure rules to classify trades in the NYSE Trade and Quote (TAQ) data as RHDW fractional share trades. Section 3 uses our sample of RHDW fractional share trades to analyze the incidence of these trades in the cross-section of U.S. publicly-traded common stocks. We also examine the correlations between the Robinhood and Drivewealth subsamples, allowing us to show the consistency of fractional share trading across brokers. Section 4 then investigates the feasibility of using the RHDW-FT metric as a proxy for app-based retail trading as well as the information content of these trades, testing empirically whether our RHDW-FT metric is predictive of a stock's future liquidity and volatility. Section 5 addresses weaknesses with respect to fractional share trade reporting in current market data, investigating censuring in the FINRA OTC Transparency data arising from FINRA's *de minimus* rule as well as volume inflation in the consolidated tape arising from the rounding-up of fractional share trades. Section 6 summarizes our results. The Appendix provides more information regarding the classification rule we use to create our sample of RHDW fractional share trades, including guidance for researchers who might seek to apply it beyond our sample period.


Section snippets
----------------

How do you find fractional share trades?
----------------------------------------

Fractional share trading occurs when a customer places an order that results in a trade confirmation indicating that the customer has acquired or sold a fraction of a whole share. In terms of the information available regarding fractional share trading, U.S. trade reporting rules create an uneven landscape at best. Some fractional share trades get reported to the public, but others do not, and those that do get reported are reported incompletely. There are a variety of reasons for this opacity, 

Who uses fractional shares? RHDW fractional share trades in the cross section
-----------------------------------------------------------------------------

A natural question to ask is whether fractional share trades matter. If retail traders use fractional share trades primarily to purchase a fraction of out-of-reach, high-priced stocks, the incidence of fractional share trades should be confined to only a small portion of U.S. equity securities. On the other hand, the emergence of fractional share trading enables retail brokerage firms to offer investors the ability to enter orders based on the dollar value of the trade rather than the number of 

Do RHDW fractional share trades contain information?
----------------------------------------------------

In this section, we explore the question of whether RHDW fractional share trades, despite their tiny size, nevertheless contain unique, value-relevant information.

Some not so tiny problems with existing data on fractional share trades
-----------------------------------------------------------------------

As the foregoing sections show, trading data for RHDW fractional share trades provides information on a distinct form of retail order flow that is relevant for predicting liquidity and volatility, but it also suffers from a number of limitations. As noted in Section 2, perhaps the largest limitation is that it reflects only a portion of fractional share trades that occur in the market, given that retail fractional share trades executed by Apex are not presently observable in the consolidated

Conclusions
-----------

Retail trading is changing and fractional shares are playing a growing role in this evolution. No longer the “nuisance” of times past, fractional shares are part of a new way of trading in which customers specify orders in dollars not shares, fintech apps sweep up spare change to invest in tiny amounts, and high share prices are no longer an impediment to retail stock ownership. Despite the growing importance of fractional share trades, our paper makes clear the challenges in understanding this 

Data availability
-----------------

Tiny Trades, Big Questions data set (Reference data) (Mendeley Data).

CRediT authorship contribution statement
----------------------------------------

**Robert P. Bartlett:** Writing – review & editing, Writing – original draft, Methodology, Investigation, Funding acquisition, Formal analysis, Conceptualization. **Justin McCrary:** Writing – review & editing, Writing – original draft, Methodology, Investigation, Funding acquisition, Formal analysis, Conceptualization. **Maureen O'Hara:** Writing – review & editing, Writing – original draft, Methodology, Investigation, Formal analysis, Conceptualization.

Declaration of competing interest
---------------------------------

Disclosure Statement – Robert Bartlett
I have nothing to disclose
Disclosure Statement – Justin McCrary
I have nothing to disclose
Disclosure Statement – Maureen O'Hara
I have nothing to disclose


Recommended articles

* J-N. Barrot *et al.*
### [Are retail trades compensated for providing liquidity?](/science/article/pii/S0304405X16000064)

### J. financ. econ.


(2016)
* R. Bartlett *et al.*
### [How rigged are stock markets? Evidence from microsecond timestamps](/science/article/pii/S1386418117302148)

### J. Financ. Markets


(2019)
* C. Lee *et al.*
### [Inferring investor behavior: evidence from TORQ data](/science/article/pii/S1386418100000021)

### J. Financ. Markets


(2000)
* M. O'Hara
### [High frequency market microstructure](/science/article/pii/S0304405X15000045)

### J. Financ. Econ.


(2015)
* B. Barber *et al.*
### A (sub)penny for your thoughts: Tracking retail activity in TAQ

### J. Finance


(2022)
* B. Barber *et al.*
### Attention induced trading and returns: Evidence from robinhood users

### J. Finance


(2022)
* B. Barber *et al.*
### Do retail trades move markets?

### Rev. Financ. Stud.


(2009)
* Bartlett, R., McCrary, J., O'Hara, M., 2022. A fractional solution to a stock market mystery, Available at SSRN:...
* Battalio, R., Jennings, R., Saglam, M., Wu, J., 2023, Identifying market maker trades as “retail’ from TAQ: No shortage...
* E. Boehmer *et al.*
### Tracking retail investor activity

### J. Finance


(2021)

- Jiafeng Chen *et al.*
### Logs with zeros? Some problems and solutions

### Quarterly J. Econ.


(2023)

View more references

* ### [Classifying the direction of Robinhood's fractional share trades](/science/article/pii/S1544612325009341)

2025, Finance Research Letters

Show abstract
I develop a novel method to sign Robinhood's fractional trades in the NYSE Daily Trade and Quote (TAQ) database. This method extends the findings of Bartlett et al. (2024) who identify Robinhood’s fractional trades in TAQ but do not sign the trades since they are executed at the National Best Bid and Offer (NBBO) midpoint. To sign the trades, I first match the fractional share trade to the corresponding whole-share trade originating from the same dollar-based order, then sign the corresponding whole-share trade using accepted retail order signing algorithms. To validate the trades’ signs, I document a significant increase in buy trades from Robinhood users immediately following stimulus check direct deposits in March 2021. This methodology significantly improves upon the state-of-the-art dataset on Robinhood user holdings which is no longer in service. The resulting data will be useful for researchers studying Robinhood or mobile investors, their actions, and their growing impacts on modern capital markets.
* ### [The Next Chapter of Big Data in Finance](https://doi.org/10.1093/rfs/hhae083)

2025, Review of Financial Studies
* ### [A Fractional Solution to a Stock Market Mystery](https://doi.org/10.1080/0015198X.2025.2489924)

2025, Financial Analysts Journal


We thank the editor Nikolai Rossanov and an anonymous referee for many helpful comments. We also thank Kevin Crotty, Elisabeth De Fontenay, Lisa Fairfax, Jill Frisch, Itay Goldstein, Frank Partnoy, Krishna Ramaswamy, Christopher Schwarz, Eric Talley, Chaojun Wang, and seminar participants at Arrowstreet Capital, UC Berkeley Law, Columbia Law, MIT, the Microstructure Exchange, the Wharton-Penn Law workshop, the SEC Division of Economic and Risk Analysis, the 2023 annual meeting of the American Law and Economics Association, and the SFS Cavalcade 2023. Research for this paper was made possible in part by the Paul J. Evanson Professorship and the Henry and Lucy Moses Faculty Research Fund at Columbia Law School.

[View full text](/science/article/pii/S0304405X2400059X)© 2024 Elsevier B.V. All rights reserved.

* ### [Discrimination in the payments chain](/science/article/pii/S0304405X24000953 "Discrimination in the payments chain")

Journal of Financial Economics, Volume 158, 2024, Article 103872
Anna M. Costello, …, Irina Rabinovich
* ### [How do Treasury dealers manage their positions?](/science/article/pii/S0304405X24001089 "How do Treasury dealers manage their positions?")

Journal of Financial Economics, Volume 158, 2024, Article 103885
Michael Fleming, …, Joshua Rosenberg
* ### [The short-termism trap: Catering to informed investors with limited horizons](/science/article/pii/S0304405X24001077 "The short-termism trap: Catering to informed investors with limited horizons")

Journal of Financial Economics, Volume 159, 2024, Article 103884
James Dow, …, Francesco Sangiorgi
* ### [Concealed carry](/science/article/pii/S0304405X24000977 "Concealed carry")

Journal of Financial Economics, Volume 159, 2024, Article 103874
Spencer Andrews, …, Federico Gavazzoni
* ### [Intermediation frictions in debt relief: Evidence from CARES Act forbearance](/science/article/pii/S0304405X24000965 "Intermediation frictions in debt relief: Evidence from CARES Act forbearance")

Journal of Financial Economics, Volume 158, 2024, Article 103873
You Suk Kim, …, James Vickery
* ### [The passive ownership share is double what you think it is](/science/article/pii/S0304405X24000837 "The passive ownership share is double what you think it is")

Journal of Financial Economics, Volume 157, 2024, Article 103860
Alex Chinco, Marco Sammon

Show 3 more articles









