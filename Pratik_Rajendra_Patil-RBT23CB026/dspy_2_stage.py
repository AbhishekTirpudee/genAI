
import dspy
import json
import time

from typing import Literal


# ==================================================
# 1. CONFIGURE LOCAL OLLAMA MODEL
# ==================================================

lm = dspy.LM(
    "ollama_chat/qwen3.5:9b",
    temperature=0
)

dspy.configure(lm=lm)

print("DSPy connected to Ollama successfully!")


# ==================================================
# 2. STAGE 1 - ENTITY EXTRACTION SIGNATURE
# ==================================================

class ExtractEntities(dspy.Signature):
    """
    Extract customer name and product name
    from an unstructured customer email.

    Rules:
    1. Extract the actual customer name.
    2. Extract the exact product name.
    3. Do not guess missing information.
    4. Return Unknown if information is unavailable.
    5. Ignore names appearing only in quoted
       previous email threads when possible.
    """

    email: str = dspy.InputField(
        desc="Complete unstructured customer email"
    )

    customer_name: str = dspy.OutputField(
        desc="Customer's name or Unknown"
    )

    product_name: str = dspy.OutputField(
        desc="Product name or Unknown"
    )


# ==================================================
# 3. STAGE 2 - COMPLAINT CLASSIFICATION SIGNATURE
# ==================================================

class ClassifyComplaint(dspy.Signature):
    """
    Classify the customer complaint.

    CATEGORY DEFINITIONS:

    Billing/Payment:
        Duplicate payment, incorrect charges,
        billing problems.

    Delivery:
        Delayed shipment, missing delivery,
        tracking problems.

    Product Defect:
        Damaged hardware, overheating,
        physical product defects.

    Technical Issue:
        Software bugs, application crashes,
        system errors.

    Account Access:
        Login failure, authentication problems,
        locked accounts, password issues.

    Refund/Return:
        Refund requests, product returns.

    Cancellation:
        Order or subscription cancellation.

    Other:
        Complaints not matching the above categories.

    PRIORITY DEFINITIONS:

    Critical:
        Safety risks, major service outages,
        severe business impact.

    High:
        Financial loss, essential functionality
        unavailable, urgent unresolved issues.

    Medium:
        Significant inconvenience with a workaround.

    Low:
        Minor or non-urgent issues.

    Do not classify based only on emotional language.
    Do not invent facts.
    """

    email: str = dspy.InputField(
        desc="Original customer email"
    )

    customer_name: str = dspy.InputField(
        desc="Extracted customer name"
    )

    product_name: str = dspy.InputField(
        desc="Extracted product name"
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
    ] = dspy.OutputField(
        desc="One standardized complaint category"
    )

    priority: Literal[
        "Critical",
        "High",
        "Medium",
        "Low"
    ] = dspy.OutputField(
        desc="One standardized priority"
    )


# ==================================================
# 4. BUILD TWO-STAGE DSPY PIPELINE
# ==================================================

class CustomerComplaintPipeline(dspy.Module):

    def __init__(self):
        super().__init__()

        # Stage 1: Extract entities
        self.entity_extractor = dspy.Predict(
            ExtractEntities
        )

        # Stage 2: Classify complaint
        self.complaint_classifier = dspy.Predict(
            ClassifyComplaint
        )

    def forward(self, email):

        # ------------------------------------------
        # STAGE 1: ENTITY EXTRACTION
        # ------------------------------------------

        print("\n[Stage 1] Extracting customer information...")

        entities = self.entity_extractor(
            email=email
        )

        customer_name = (
            entities.customer_name.strip()
            if entities.customer_name
            else "Unknown"
        )

        product_name = (
            entities.product_name.strip()
            if entities.product_name
            else "Unknown"
        )

        print("Customer:", customer_name)
        print("Product :", product_name)

        # ------------------------------------------
        # STAGE 2: COMPLAINT CLASSIFICATION
        # ------------------------------------------

        print("\n[Stage 2] Classifying complaint...")

        classification = self.complaint_classifier(
            email=email,
            customer_name=customer_name,
            product_name=product_name
        )

        # ------------------------------------------
        # FINAL STRUCTURED OUTPUT
        # ------------------------------------------

        return dspy.Prediction(
            customer_name=customer_name,
            product_name=product_name,
            complaint_category=classification.complaint_category,
            priority=classification.priority
        )


# ==================================================
# 5. TEST THE PIPELINE
# ==================================================

if __name__ == "__main__":

    email = """
    Subject: Unable to Access My Account

    Hello Support Team,

    My name is Karan Mehta.

    I have been using CloudDesk for six months.
    Since yesterday, I cannot log in to my account.

    The application displays an Authentication Failed
    error even after resetting my password.

    I need access because I have an important
    client presentation tomorrow.

    Please resolve this issue urgently.

    Regards,
    Karan Mehta
    """

    # Initialize pipeline
    pipeline = CustomerComplaintPipeline()

    # Measure execution time
    start_time = time.perf_counter()

    try:

        result = pipeline(email=email)

        end_time = time.perf_counter()

        # Convert prediction to dictionary
        output = {
            "customer_name": result.customer_name,
            "product_name": result.product_name,
            "complaint_category": result.complaint_category,
            "priority": result.priority
        }

        # ------------------------------------------
        # DISPLAY RESULTS
        # ------------------------------------------

        print("\n" + "=" * 45)
        print("CUSTOMER COMPLAINT EXTRACTION")
        print("=" * 45)

        print(json.dumps(output, indent=4))

        print("\nExecution Time:",
              round(end_time - start_time, 2), "seconds")

        print("\nSUCCESS: Two-stage pipeline completed!")

    except Exception as error:

        print("\nPIPELINE FAILED!")
        print("Error:", error)

