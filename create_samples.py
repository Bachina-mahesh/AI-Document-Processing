import os

def create_sample_documents():
    os.makedirs("sample_documents", exist_ok=True)
    
    documents = {
        "invoice.txt": """INVOICE
Invoice #: INV-2024-001
Date: January 15, 2024

From: ABC Corporation, 123 Business St, New York, NY 10001
To: XYZ Company, 456 Client Ave, Los Angeles, CA 90001

Items:
1. Software License - Professional: $999.00
2. Support Services (Annual): $299.00
3. Training Package: $500.00

Subtotal: $1,798.00
Tax (8%): $143.84
Total: $1,941.84

Payment Terms: Net 30
Due: February 15, 2024""",

        "contract.txt": """SERVICE AGREEMENT
Date: January 1, 2024

PARTIES:
Provider: TechServices Inc. (Delaware)
Client: GlobalCorp Ltd. (California)

TERM: 12 months (Jan 1 - Dec 31, 2024)

SERVICES:
- 24/7 cloud monitoring
- Security updates
- Monthly reports

COMPENSATION: $5,000/month (due 1st of month)

OBLIGATIONS:
- 99.9% uptime SLA
- Access credentials within 5 days

SIGNATURES: [To be signed]""",

        "purchase_order.txt": """PURCHASE ORDER
PO #: PO-2024-0055
Date: January 10, 2024

Vendor: Office Supplies Direct
Ship To: Corporate Office, SF

Items:
1. Office Chairs (25) @ $350 = $8,750
2. Standing Desks (15) @ $650 = $9,750
3. Monitor Arms (40) @ $120 = $4,800

Subtotal: $23,300
Shipping: $500
Total: $23,800

Delivery: January 25, 2024
Terms: Net 45""",

        "mixed_document.txt": """QUARTERLY REPORT Q4 2023

Financial summary...

---EMBEDDED INVOICE---
Invoice: INV-Q4-999
Services: Consulting Q4
Amount: $50,000
Due: 30 days
---END INVOICE---

Also confirms contract renewal:
Contract Value: $150,000 for 2024""",

        "incomplete_spec.txt": """TECHNICAL SPECIFICATION
Product: Advanced Widget Pro
Version: 3.

Specifications:
- Dimensions: 10cm x 15cm x
- Weight: [MISSING]
- Power: 120V AC
- Interface:

Requirements:
- OS: Windows 10 or
- RAM: 8GB
- Storage:

[TRUNCATED]"""
    }
    
    for filename, content in documents.items():
        with open(f"sample_documents/{filename}", 'w') as f:
            f.write(content.strip())
    
    print("✅ Sample documents created in 'sample_documents/' folder")

if __name__ == "__main__":
    create_sample_documents()