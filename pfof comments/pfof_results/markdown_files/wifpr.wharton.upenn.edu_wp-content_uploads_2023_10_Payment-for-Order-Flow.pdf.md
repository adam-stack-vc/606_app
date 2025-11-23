---
                title: "('Payment for Order Flow and the Retail Trading Experience',)"
                url: "https://wifpr.wharton.upenn.edu/wp-content/uploads/2023/10/Payment-for-Order-Flow.pdf"
                date: ""
                sentiment: "('Neutral, Negative',)"
                topic: "pfof"
                ---


  "response": "Earliest PFOF observed: 1/2020 (total $26,300,210.88). Examples: Open to the Public Investing, Inc. (1/2020), Apex Investing (1/2020), BofA Securities, Inc. (1/2020)",


{
  "question": "list the month and year for the earliest record of each broker receiving PFOF.",
  "sql": "Multiple queries executed",
  "query_results": {
    "pfof_data": {
      "description": "PFOF payment data from executing_bd_606",
      "query": "\n    SELECT \n        executing_bd,\n        venues,\n        SUM(COALESCE(netpmtpaidrecvmarketordersusd, 0) +\n            COALESCE(netpmtpaidrecvmarketablelimitordersusd, 0) +\n            COALESCE(netpmtpaidrecvnonmarketablelimitordersusd, 0) +\n            COALESCE(netpmtpaidrecvotherordersusd, 0)) as total_pfof_usd,\n        AVG(COALESCE(netpmtpaidrecvmarketorderscph, 0) +\n            COALESCE(netpmtpaidrecvmarketablelimitorderscph, 0) +\n            COALESCE(netpmtpaidrecvnonmarketablelimitorderscph, 0) +\n            COALESCE(netpmtpaidrecvotherorderscph, 0)) as avg_cph\n    FROM executing_bd_606\n    WHERE data_type = 'venue'\n    GROUP BY executing_bd, venues\n    ORDER BY total_pfof_usd DESC\n    LIMIT 10;\n    ",
      "results": [
        {
          "executing_bd": "Robinhood Securities, LLC",
          "venues": "CITADEL SECURITIES LLC",
          "total_pfof_usd": 951858432.5,
          "avg_cph": 153.85076923076923
        },
        {
          "executing_bd": "Charles Schwab",
          "venues": "CITADEL SECURITIES LLC",
          "total_pfof_usd": 928885718.62,
          "avg_cph": 90.44491228070176
        },
        {
          "executing_bd": "Robinhood Securities LLC",
          "venues": "CITADEL SECURITIES LLC",
          "total_pfof_usd": 466761923.11,
          "avg_cph": 162.008
        },
        {
          "executing_bd": "TD Ameritrade Clearing, Inc",
          "venues": "CITADEL SECURITIES LLC",
          "total_pfof_usd": 450358140.02,
          "avg_cph": 87.39840579710145
        },
        {
          "executing_bd": "Robinhood Securities, LLC",
          "venues": "Dash/IMC Financial Markets",
          "total_pfof_usd": 447267566.75,
          "avg_cph": 202
        },
        {
          "executing_bd": "TD Ameritrade Clearing, Inc",
          "venues": "Global Execution Brokers LP",
          "total_pfof_usd": 383737167.17,
          "avg_cph": 195.3984210526316
        },
        {
          "executing_bd": "Robinhood Securities, LLC",
          "venues": "Wolverine Execution Services, LLC",
          "total_pfof_usd": 368237577.73,
          "avg_cph": 198.89153846153846
        },
        {
          "executing_bd": "Charles Schwab",
          "venues": "Dash/IMC Financial Markets",
          "total_pfof_usd": 361653421.66,
          "avg_cph": 182.44377777777777
        },
        {
          "executing_bd": "TD Ameritrade Clearing, Inc",
          "venues": "Citadel Securities, LLC",
          "total_pfof_usd": 355584486,
          "avg_cph": 115.22155555555555
        },
        {
          "executing_bd": "Charles Schwab",
          "venues": "Global Execution Brokers LP",
          "total_pfof_usd": 354933472.57,
          "avg_cph": 191.94
        }
      ],
      "row_count": 10
    },
    "market_data": {
      "description": "Market volume data from monthly_data",
      "query": "\n    SELECT \n        market_participant,\n        SUM(total_shares) as total_shares,\n        SUM(total_notional) as total_notional,\n        SUM(total_trade_count) as total_trades,\n        COUNT(DISTINCT day) as trading_days\n    FROM monthly_data\n    \n    GROUP BY market_participant\n    ORDER BY total_shares DESC\n    LIMIT 10;\n    ",
      "results": [
        {
          "market_participant": "FINRA / Nasdaq TRF Carteret (DQ)",
          "total_shares": 7820415127094,
          "total_notional": 352244021545726.25,
          "total_trades": 34351236177,
          "trading_days": 1939
        },
        {
          "market_participant": "NASDAQ (Q)",
          "total_shares": 6164266307621,
          "total_notional": 297270006884147.2,
          "total_trades": 42891154835,
          "trading_days": 4204
        },
        {
          "market_participant": "NASDAQ (DQ)",
          "total_shares": 5309770229987,
          "total_notional": 162535356515343.9,
          "total_trades": 13712861895,
          "trading_days": 2265
        },
        {
          "market_participant": "NYSE (N)",
          "total_shares": 4729925054911,
          "total_notional": 174790457475513.78,
          "total_trades": 16043508670,
          "trading_days": 4502
        },
        {
          "market_participant": "NYSE Arca (P)",
          "total_shares": 4341318872003,
          "total_notional": 173632626704922.03,
          "total_trades": 24216800479,
          "trading_days": 4502
        },
        {
          "market_participant": "EDGX Equities (K)",
          "total_shares": 1326631630527,
          "total_notional": 54471807376264.66,
          "total_trades": 8666457588,
          "trading_days": 2190
        },
        {
          "market_participant": "FINRA / NYSE TRF (DN)",
          "total_shares": 1309895019423,
          "total_notional": 43689079839475.67,
          "total_trades": 4141488180,
          "trading_days": 1939
        },
        {
          "market_participant": "BZX Equities (Z)",
          "total_shares": 1118043749311,
          "total_notional": 60669354878905.91,
          "total_trades": 10598503646,
          "trading_days": 2190
        },
        {
          "market_participant": "BATS BZX (Z)",
          "total_shares": 1038002476688,
          "total_notional": 38507857747502.44,
          "total_trades": 5972705249,
          "trading_days": 1762
        },
        {
          "market_participant": "Nasdaq (Q)",
          "total_shares": 761772365140,
          "total_notional": 7225613264441.7,
          "total_trades": 3433987771,
          "trading_days": 298
        }
      ],
      "row_count": 10
    },
    "earliest_pfof_month": {
      "description": "Earliest month/year with PFOF > 0",
      "query": "\nWITH by_month AS (\n  SELECT\n    year,\n    month,\n    SUM(\n      COALESCE(netpmtpaidrecvmarketordersusd, 0) +\n      COALESCE(netpmtpaidrecvmarketablelimitordersusd, 0) +\n      COALESCE(netpmtpaidrecvnonmarketablelimitordersusd, 0) +\n      COALESCE(netpmtpaidrecvotherordersusd, 0)\n    ) AS total_pfof_usd\n  FROM executing_bd_606\n  WHERE data_type = 'venue'\n  GROUP BY year, month\n)\nSELECT year, month, total_pfof_usd\nFROM by_month\nWHERE total_pfof_usd > 0\nORDER BY year ASC, (NULLIF(month, '')::int) ASC\nLIMIT 1;\n",
      "results": [
        {
          "year": 2020,
          "month": "1",
          "total_pfof_usd": 26300210.88
        }
      ],
      "row_count": 1
    },
    "earliest_pfof_by_broker": {
      "description": "Earliest month/year with PFOF > 0 per broker",
      "query": "\nWITH by_broker_month AS (\n  SELECT\n    executing_bd,\n    year,\n    month,\n    SUM(\n      COALESCE(netpmtpaidrecvmarketordersusd, 0) +\n      COALESCE(netpmtpaidrecvmarketablelimitordersusd, 0) +\n      COALESCE(netpmtpaidrecvnonmarketablelimitordersusd, 0) +\n      COALESCE(netpmtpaidrecvotherordersusd, 0)\n    ) AS total_pfof_usd\n  FROM executing_bd_606\n  WHERE data_type = 'venue'\n    AND executing_bd IS NOT NULL AND executing_bd != ''\n  GROUP BY executing_bd, year, month\n), first_paid AS (\n  SELECT\n    executing_bd,\n    year,\n    month,\n    total_pfof_usd,\n    ROW_NUMBER() OVER (\n      PARTITION BY executing_bd\n      ORDER BY year ASC, (NULLIF(month,'')::int) ASC\n    ) AS rn\n  FROM by_broker_month\n  WHERE total_pfof_usd > 0\n)\nSELECT executing_bd, year, month, total_pfof_usd\nFROM first_paid\nWHERE rn = 1\nORDER BY year ASC, (NULLIF(month,'')::int) ASC\nLIMIT 50;\n",
      "results": [
        {
          "executing_bd": "Open to the Public Investing, Inc.",
          "year": 2020,
          "month": "1",
          "total_pfof_usd": 933.59
        },
        {
          "executing_bd": "Apex Investing",
          "year": 2020,
          "month": "1",
          "total_pfof_usd": 1508330.35
        },
        {
          "executing_bd": "BofA Securities, Inc.",
          "year": 2020,
          "month": "1",
          "total_pfof_usd": 574836.72
        },
        {
          "executing_bd": "Webull Financial LLC",
          "year": 2020,
          "month": "1",
          "total_pfof_usd": 625586.53
        },
        {
          "executing_bd": "Citigroup",
          "year": 2020,
          "month": "1",
          "total_pfof_usd": 2712708.58
        },
        {
          "executing_bd": "UBS Securities, LLC",
          "year": 2020,
          "month": "1",
          "total_pfof_usd": 1468872.61
        },
        {
          "executing_bd": "StoneX Financial, Inc.",
          "year": 2020,
          "month": "1",
          "total_pfof_usd": 38489.65
        },
        {
          "executing_bd": "Dough",
          "year": 2020,
          "month": "1",
          "total_pfof_usd": 181.32
        },
        {
          "executing_bd": "Robinhood Securities",
          "year": 2020,
          "month": "1",
          "total_pfof_usd": 19370271.53
        },
        {
          "executing_bd": "WALL STREET ACCESS",
          "year": 2020,
          "month": "4",
          "total_pfof_usd": 9077.95
        },
        {
          "executing_bd": "Citigroup Global Markets Inc.",
          "year": 2020,
          "month": "4",
          "total_pfof_usd": 979815.91
        },
        {
          "executing_bd": "Charles Schwab",
          "year": 2020,
          "month": "4",
          "total_pfof_usd": 21482620.97
        },
        {
          "executing_bd": "Robinhood Securities LLC",
          "year": 2020,
          "month": "7",
          "total_pfof_usd": 67320280.86
        },
        {
          "executing_bd": "MLCO_606",
          "year": 2020,
          "month": "7",
          "total_pfof_usd": 1039238.18
        },
        {
          "executing_bd": "DOUGH, LLC",
          "year": 2020,
          "month": "7",
          "total_pfof_usd": 15930.03
        },
        {
          "executing_bd": "Wedbush Securities, Inc.",
          "year": 2020,
          "month": "10",
          "total_pfof_usd": 19518.75
        },
        {
          "executing_bd": "MLCO.606",
          "year": 2020,
          "month": "10",
          "total_pfof_usd": 1843075.03
        },
        {
          "executing_bd": "TD Ameritrade Clearing, Inc",
          "year": 2021,
          "month": "4",
          "total_pfof_usd": 55071168
        },
        {
          "executing_bd": "TD Ameritrade, Inc.",
          "year": 2021,
          "month": "4",
          "total_pfof_usd": 48947265
        },
        {
          "executing_bd": "APEX Clearing",
          "year": 2021,
          "month": "10",
          "total_pfof_usd": 2700467.69
        },
        {
          "executing_bd": "Cannacord Genuity Inc.",
          "year": 2022,
          "month": "4",
          "total_pfof_usd": 11662.25
        },
        {
          "executing_bd": "Robinhood Securities, LLC",
          "year": 2022,
          "month": "4",
          "total_pfof_usd": 47278817.32
        },
        {
          "executing_bd": "CIBC World Markets Corp.",
          "year": 2022,
          "month": "10",
          "total_pfof_usd": 22083.29
        },
        {
          "executing_bd": "Citigroup Global Markets Inc. (ICG Markets)",
          "year": 2023,
          "month": "4",
          "total_pfof_usd": 305659.67
        },
        {
          "executing_bd": "Altruist Financial LLC",
          "year": 2023,
          "month": "4",
          "total_pfof_usd": 4712.12
        },
        {
          "executing_bd": "Citigroup Global Markets Inc. (Citigroup Wealth Management)",
          "year": 2023,
          "month": "7",
          "total_pfof_usd": 33.58
        },
        {
          "executing_bd": "Citigroup Global Markets Inc. (Institutional)",
          "year": 2023,
          "month": "10",
          "total_pfof_usd": 467284.53
        },
        {
          "executing_bd": "RBC Capital Markets Corporation",
          "year": 2023,
          "month": "10",
          "total_pfof_usd": 568.02
        },
        {
          "executing_bd": "Citigroup Global Markets Inc. (Retail)",
          "year": 2023,
          "month": "10",
          "total_pfof_usd": 901.92
        },
        {
          "executing_bd": "MLCO.GBAM",
          "year": 2024,
          "month": "4",
          "total_pfof_usd": 586144.29
        },
        {
          "executing_bd": "GPC",
          "year": 2024,
          "month": "10",
          "total_pfof_usd": 141.84
        },
        {
          "executing_bd": "Citigroup Global Markets Inc. (Markets)",
          "year": 2025,
          "month": "4",
          "total_pfof_usd": 339859.42
        }
      ],
      "row_count": 32
    }
  },
  "response": "Earliest PFOF observed: 1/2020 (total $26,300,210.88). Examples: Open to the Public Investing, Inc. (1/2020), Apex Investing (1/2020), BofA Securities, Inc. (1/2020)",
  "query_type": "complex_multi_table",
  "query_classification": {
    "mentions_volume": false,
    "mentions_pfof": true,
    "mentions_order_type": false,
    "ambiguous_paid": false,
    "mentions_rate": false,
    "mentions_cph": false,
    "mentions_max": false,
    "mentions_zero_pfof": false,
    "mentions_month": true,
    "mentions_year": true,
    "mentions_quarter": false,
    "mentions_broker": true,
    "mentions_venue": false,
    "mentions_trend": false,
    "mentions_ats": false,
    "mentions_tape": false,
    "mentions_market_share": false,
    "mentions_entity_type": false,
    "mentions_streak": false,
    "mentions_longest": true,
    "mentions_first": true,
    "mentions_orders": false,
    "year": null,
    "month": null,
    "quarter": null,
    "executing_bd": null,
    "venue": "Israel A. Englander & Co., Inc.",
    "stock_group": null
  },
  "row_count": 53
}
                