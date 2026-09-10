---------
CCP12 White paper highlights:
---------
Distinction between the market participants here: 
- Central Counterparty - Clearing houses like CME
- Clearing members - bsaically the big banks and other institutions that have direct access to the clearing house.


Basic Highlights:
---------
- EMIR/RTS Article 24; floor of 99% confidence intervals for exchange traded derivative instruments, 99.5% for OTC traded deriavtives
- MPOR(Margin Period of Risk) - this is basically the number of days over we are measuring the tail losses(1-day and 5-day only defined).
- Default waterfall:
	- Defaulter's Margin: the defaulter's initial margin plus any excess collateral on deposit, plus VM that was due and unpaid at default.
	- Defaulter's Contribution: defaulter's prefunded default fund contribution 
	- CCP's Skin-in-the-Game: this is a designated portion of the clearing house's own capital that is used to cover the losses due to default.
	- Surviving Member's funds
	- Assessments: Assessment powers are contractual, capped rights to call additional funds from surviving members
- Variation/Maintenance Margin is settled daily; the defaulter's initial margin + excess collateral on deposit + the variation margin that is due/unpaid at default


Final Statement:
---------
Initial margin is sized to absorb tail losses over 1 or 5 day MPOR, at 99% confidence for exchange traded derivatives and 99.5% for OTC derivatives, so that the defaulting clearing member's own resources absorb the loss rather than surviving members or the CCP.


Structure:
---------
	Layer 01: Defaulter Pays
		|
		|
	Layer 03: Skin-in-the-Game(CCP contribution)
		|
		|
	Layer 02: Mutualized payments(Survivors+Defaulters)




---------
SPAN2 Framework:
---------

Terminology:
---------
Lookback period: This is the timeframe that is used to evaluate tail losses.


What risk is each of the following components paid for?
- Historical Risk HVaR:Assess the tail losses a portfolio can incur due to daily price movements over a lookback period during the MPOR; additional returns analysis is done with scenario generation from vol and corr scaling & HVaR is take as the tail loss over the full PnL distributions across all scenarios.
- Stress Risk SVaR: HVaR is restricted to evaluating tail losses considering only the stressed periods of that have already occurred; SVaR is used as an additional tool for PMs to assess what kind of tail losses can take place by generating scenarios and SVaR is calculated as the tail loss of the full PnL distribution that is generated based on different scenarios(SVaR fro stress period simulations of events that occurred the lookback window and Hypothetical SVaR for hypothetical scenarios). 
- Liquidity:Liquidity charges capture the close out costs calculated during default, based on the available Bid/Ask spreads from teh central limit order book. Open interest is also considered in clauculating the Liquidation parameters.
- Concentration: Concentration costs are for large portfolios that are beyod a certain threshold.






















