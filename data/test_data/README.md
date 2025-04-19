# EU AI Act Compliance Analysis Test Data

This directory contains sample AI system documentation for testing the EU AI Act Compliance Analysis Tool. The documentation is organized by system risk category as defined in the EU AI Act.

## Directory Structure

```
test_data/
├── prohibited/             # Systems prohibited under Article 5
│   └── social_scoring_system.md
├── high_risk/              # High-risk systems under Articles 6 & 7
│   └── medical_diagnosis_system.md
├── limited_risk/           # Limited-risk systems with transparency requirements
│   └── customer_service_chatbot.md
└── minimal_risk/           # Minimal-risk systems
    └── product_recommendation_engine.md
```

## Test Cases

### Prohibited Systems
- `social_scoring_system.md`: An AI system for social credit scoring that should be classified as prohibited under Article 5 of the EU AI Act.

### High-Risk Systems
- `medical_diagnosis_system.md`: A medical diagnosis AI system that should be classified as high-risk due to its use in healthcare.

### Limited-Risk Systems
- `customer_service_chatbot.md`: A customer service chatbot that should be classified as limited-risk due to transparency requirements.

### Minimal-Risk Systems
- `product_recommendation_engine.md`: A product recommendation engine for e-commerce that should be classified as minimal-risk.

## Using the Test Data

These test files are used by the test suite runner (`src/run_test_suite.py`) to validate the compliance analyzer's ability to correctly classify different types of AI systems and generate appropriate compliance reports.

To run tests with this data:

```bash
python -m src.run_test_suite
```

## Adding New Test Cases

To add new test cases:

1. Create a new markdown file in the appropriate risk category directory
2. Follow the documentation structure of existing test files
3. Include clear signals in the documentation that would help classify the system into the intended risk category
4. Make sure the file has the .md extension 