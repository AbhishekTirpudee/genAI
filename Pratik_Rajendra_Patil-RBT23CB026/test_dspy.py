
import dspy

# -----------------------------------------
# 1. Configure local Ollama model
# -----------------------------------------

lm = dspy.LM(
    "ollama_chat/qwen3.5:9b",
    temperature=0
)

dspy.configure(lm=lm)

print("DSPy configured with Ollama!")


# -----------------------------------------
# 2. Define extraction signature
# -----------------------------------------

class CustomerComplaint(dspy.Signature):
    """
    Extract four fields from a customer email.

    Do not guess missing information.
    Use Unknown when information is unavailable.
    """

    email: str = dspy.InputField()

    customer_name: str = dspy.OutputField(
        desc="Customer name or Unknown"
    )

    product_name: str = dspy.OutputField(
        desc="Product name or Unknown"
    )

    complaint_category: str = dspy.OutputField(
        desc="Complaint category"
    )

    priority: str = dspy.OutputField(
        desc="Priority: Critical, High, Medium, or Low"
    )


# -----------------------------------------
# 3. Create DSPy predictor
# -----------------------------------------

extractor = dspy.Predict(CustomerComplaint)


# -----------------------------------------
# 4. Test customer email
# -----------------------------------------

email = """
Subject: Unable to Access My Account – Login Error

Hello Support Team,

My name is Karan Mehta.

I have been using your CloudDesk application for
the past six months. Since yesterday evening,
I have been unable to log in to my account.

Whenever I enter my correct email address and
password, the application displays an
"Authentication Failed" error.

I have already tried resetting my password,
clearing the browser cache, and logging in from
another device, but the problem still persists.

I need access to my account because I have an
important client presentation tomorrow.

Please look into this issue urgently.

Regards,
Karan Mehta
"""


# -----------------------------------------
# 5. Run extraction
# -----------------------------------------

print("\nSending email to local Qwen model...")

try:
    result = extractor(email=email)

    print("\n========== EXTRACTION RESULT ==========")

    print("Customer Name :", result.customer_name)
    print("Product Name  :", result.product_name)
    print("Category      :", result.complaint_category)
    print("Priority      :", result.priority)

    print("\n========== TEST STATUS ==========")
    print("SUCCESS: DSPy + Ollama inference completed!")

except Exception as error:
    print("\nTEST FAILED!")
    print("Error:", error)

