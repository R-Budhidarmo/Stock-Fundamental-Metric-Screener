# Stock Fundamental Metric Screener

The code in ```screen.py``` serves as a proof-of-concept (POC) app to allow a user to quickly evaluate fundamental (accounting data-related) data metrics about a publicly-traded company. As long the ticker symbol & the company's data are available from [Yahoo Finance](https://finance.yahoo.com/), the user will be able to examine some key financial metrics.

---

## Installation

To run the code, you need to have Python 3.x installed (Python 3.11 was used during development) and several common libraries: ```datetime```, ```numpy```, ```pandas```, ```yahooquery```, and ```yfinance```. They can be simply installed as follows:

```bash
pip install -r requirements.txt
```

---

## Usage

To run the code, simply execute the `screen.py` script from the command line:

```bash
python screen.py
```

Follow the prompts to interact with the app & input the ticker symbol and the frequency of data to be retrieved. Some output examples are shown below:

![Quarterly Data](https://github.com/R-Budhidarmo/Stock-Fundamental-Metric-Screener/blob/main/output_quarterly.png)
![Annual Data](https://github.com/R-Budhidarmo/Stock-Fundamental-Metric-Screener/blob/main/output_annual.png)
---

## Disclaimer

The code was developed for educational purposes only. Any outputs that the code may produce must not be treated as absolute investment advice. When in doubt, seek help from a professional financial adviser. In addition, there may be bugs popping up depending on how the data are retrieved by ```yahooquery``` or ```yfinance```, and depending on how different companies structured their financial reports. Feel free to fork it and change things to suit your needs.
