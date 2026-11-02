
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from mlxtend.frequent_patterns import apriori, association_rules

# Page configuration
st.set_page_config(page_title="Apriori Analysis", page_icon="🛒", layout="wide")

# Frontend
st.title("🛒 Market Basket Analysis")
st.subheader("Apriori Algorithm")
st.write("Find frequently purchased products using association rules.")

# Sidebar settings
st.sidebar.header("Algorithm Settings")
support = st.sidebar.slider("Minimum Support", 0.01, 0.5, 0.01)
confidence = st.sidebar.slider("Minimum Confidence", 0.1, 1.0, 0.2)

# Upload dataset
st.header("1. Upload Dataset")
file = st.file_uploader("Upload Kaggle CSV file", type=["csv"])

if file is not None:

    df = pd.read_csv(file)

    st.success("Dataset uploaded successfully!")
    st.subheader("Dataset Preview")
    st.dataframe(df.head())

    # Backend preprocessing
    required = ["Member_number", "Date", "itemDescription"]

    if not all(col in df.columns for col in required):
        st.error("Please upload the Groceries dataset with the correct columns.")

    else:
        df = df.dropna(subset=required).copy()

        df["Transaction"] = (
            df["Member_number"].astype(str) + "_" +
            df["Date"].astype(str)
        )

        basket = df.groupby(
            ["Transaction", "itemDescription"]
        ).size().unstack(fill_value=0)

        basket = (basket > 0).astype(int)

        st.header("2. Preprocessed Dataset")
        st.dataframe(basket.head())

        # Run Apriori
        if st.button("Run Apriori Algorithm"):

            frequent = apriori(
                basket,
                min_support=support,
                use_colnames=True
            )

            st.header("3. Frequent Itemsets")

            if frequent.empty:
                st.warning("No frequent itemsets found. Reduce minimum support.")

            else:
                frequent["Items"] = frequent["itemsets"].apply(
                    lambda x: ", ".join(sorted(x))
                )

                frequent_output = frequent[["Items", "support"]]
                st.dataframe(frequent_output)

                st.header("4. Association Rules")

                if frequent["itemsets"].apply(len).max() >= 2:

                    rules = association_rules(
                        frequent,
                        metric="confidence",
                        min_threshold=confidence
                    )

                else:
                    rules = pd.DataFrame()

                if rules.empty:
                    st.warning("No association rules found. Reduce minimum confidence.")

                else:
                    rules["Antecedents"] = rules["antecedents"].apply(
                        lambda x: ", ".join(sorted(x))
                    )
                    rules["Consequents"] = rules["consequents"].apply(
                        lambda x: ", ".join(sorted(x))
                    )

                    output = rules[
                        ["Antecedents", "Consequents",
                         "support", "confidence", "lift"]
                    ]

                    st.dataframe(output)

                # Dashboard
                st.header("5. Analysis Dashboard")

                c1, c2, c3 = st.columns(3)

                c1.metric("Transactions", len(basket))
                c2.metric("Products", len(basket.columns))
                c3.metric("Frequent Itemsets", len(frequent))

                # Visualization
                st.header("6. Visualization")

                top = frequent.sort_values(
                    "support", ascending=False
                ).head(10)

                if not top.empty:
                    fig, ax = plt.subplots(figsize=(10, 5))

                    labels = top["itemsets"].apply(
                        lambda x: ", ".join(sorted(x))
                    )

                    ax.barh(labels, top["support"])
                    ax.set_xlabel("Support")
                    ax.set_title("Top 10 Frequent Itemsets")
                    ax.invert_yaxis()

                    st.pyplot(fig)
                    plt.close(fig)

                # Download
                st.header("7. Download Results")

                st.download_button(
                    "Download Frequent Itemsets",
                    frequent_output.to_csv(index=False),
                    "frequent_itemsets.csv"
                )

                if not rules.empty:
                    st.download_button(
                        "Download Association Rules",
                        output.to_csv(index=False),
                        "association_rules.csv"
                    )

                st.success("Apriori Analysis Completed Successfully!")
