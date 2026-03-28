
import streamlit as st

st.set_page_config(page_title="Grocery Shopper", page_icon="🛒", layout="wide")

st.title("🛒 Grocery Shopper")
st.subheader("Precision shopping planner")

items = st.text_area(
    "Enter one shopping item per line",
    placeholder="milk\nrice\nbeans\nchicken nuggets",
    height=200
)

budget = st.number_input("Enter your budget (£)", min_value=0.0, value=20.0, step=1.0)

if st.button("Process shopping list"):
    parsed_items = [item.strip() for item in items.splitlines() if item.strip()]

    if not parsed_items:
        st.warning("Please enter at least one item.")
    else:
        st.success("Shopping list captured successfully.")
        st.write("### Your items")
        for i, item in enumerate(parsed_items, start=1):
            st.write(f"{i}. {item}")

        st.write(f"### Budget: £{budget:.2f}")
