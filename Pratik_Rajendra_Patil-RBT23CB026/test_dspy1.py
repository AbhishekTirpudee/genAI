
import dspy
from typing import Literal

# -----------------------------------------
# 1. Configure Ollama + Qwen
# -----------------------------------------

lm = dspy.LM(
    "ollama_chat/qwen3.5:9b",
    temperature=0
)

dspy.configure(lm=lm)

print("DSPy configured with Ollama!")


# -----------------------------------------
# 2. Define standardized extraction
# -----------------------------------------

class CustomerComplaint(dspy.Signature):
    """
    Extract customer information and classify
    the complaint using ONLY the allowed labels.

    CATEGORY RULES:

    Billing/Payment:
        Duplicate payment, incorrect charges, billing.

    Delivery:
        Late delivery, missing shipment, tracking.

    Product Defect:
        Damaged hardware, overheating, physical defects.

    Technical Issue:
        Software crashes, application errors, bugs.

    Account Access:
        Login errors, authentication failures,
        locked accounts, password problems.

    Refund/Return:
        Refund requests, product returns.

    Cancellation:
        Order or subscription cancellation.

    Other:
        Anything that does not fit above.

    PRIORITY RULES:

    Critical: Safety risks, major outages,
              severe business impact.

    High: Important functionality unavailable,
          financial loss, urgent unresolved issue.

    Medium: Significant inconvenience with
            a workaround available.

    Low: Minor or non-urgent issue.

    Never invent missing customer or product details.
    Use Unknown when information is unavailable.
    """

    email: str = dspy.InputField()

    customer_name: str = dspy.OutputField(
        desc="Customer name or Unknown"
    )

    product_name: str = dspy.OutputField(
        desc="Product name or Unknown"
    )

    complaint_category: Literal[
        "Billing/Payment",
        "Delivery",
        "Product Defect",
        "Technical Issue",
        "Account Access",
        "Refund/Return",
        "Cancellation",
        "Other"
    ] = dspy.OutputField()

    priority: Literal[
        "Critical",
        "High",
        "Medium",
        "Low"
    ] = dspy.OutputField()


# -----------------------------------------
# 3. Initialize predictor
# -----------------------------------------

extractor = dspy.Predict(CustomerComplaint)


# -----------------------------------------
# 4. Test email
# -----------------------------------------

email = """
Subject: Unable to Access My Account

My name is Karan Mehta.

I have been using CloudDesk for six months.
Since yesterday, I cannot log in to my account.

The application displays an Authentication Failed
error even after resetting my password.

I need access because I have an important
client presentation tomorrow.

Please resolve this urgently.

Regards,
Karan Mehta
"""


# -----------------------------------------
# 5. Execute pipeline
# -----------------------------------------

print("\nProcessing customer email...")

try:
    result = extractor(email=email)

    print("\n========== EXTRACTION RESULT ==========")

    print("Customer Name :", result.customer_name)
    print("Product Name  :", result.product_name)
    print("Category      :", result.complaint_category)
    print("Priority      :", result.priority)

    print("\nSUCCESS: Standardized extraction completed!")

except Exception as error:
    print("\nExtraction failed!")
    print(error)

