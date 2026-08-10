GROUND_TRUTH = {
    "sample_contract.pdf": {
        "parties": [
            {"name": "Northwind Logistics Inc.", "role": "Client"},
            {"name": "Cascade Data Solutions LLC", "role": "Vendor"},
        ],
        "clauses": {
            "effective_date": {"date": "2026-03-01"},
            "renewal_date": {"date": "2027-03-01"},
            "notice_period": {"days": 60},
        },
        "termination_keywords": ["30", "90", "breach", "convenience"],
        "absent_clause_types": ["payment_terms"],
    },
    "sample_contract_2.docx": {
        "parties": [
            {"name": "Meridian Manufacturing Co.", "role": "Lessee"},
            {"name": "Atlas Industrial Rentals LLC", "role": "Lessor"},
        ],
        "clauses": {
            "effective_date": {"date": "2026-06-15"},
            "renewal_date": {"date": "2028-06-15"},
            "notice_period": {"days": 45},
        },
        "termination_keywords": ["15", "insolvent", "bankruptcy"],
        "absent_clause_types": ["payment_terms"],
    },
}