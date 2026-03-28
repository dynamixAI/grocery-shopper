import streamlit as st
import pandas as pd


st.set_page_config(
    page_title="Grocery Shopper",
    page_icon="🛒",
    layout="wide"
)


def parse_items(raw_text: str) -> list[str]:
    """
    Clean and standardise user-entered shopping items.

    Rules:
    - split by line
    - trim spaces
    - remove blank rows
    - remove duplicates while preserving order
    - convert repeated internal spaces to single spaces
    """
    lines = raw_text.splitlines()
    cleaned_items = []

    for line in lines:
        item = " ".join(line.strip().split())
        if item:
            cleaned_items.append(item)

    unique_items = list(dict.fromkeys(cleaned_items))
    return unique_items


def initialise_session() -> None:
    """Create session state variables if they do not already exist."""
    if "parsed_items" not in st.session_state:
        st.session_state.parsed_items = []

    if "selected_stores" not in st.session_state:
        st.session_state.selected_stores = []

    if "location" not in st.session_state:
        st.session_state.location = ""

    if "budget" not in st.session_state:
        st.session_state.budget = 0.0


def main() -> None:
    initialise_session()

    st.title("🛒 Grocery Shopper")
    st.subheader("Precision shopping planner")
    st.write(
        "Enter the items you want, choose the stores to compare, and prepare your basket."
    )

    with st.sidebar:
        st.header("Shopping Settings")

        selected_stores = st.multiselect(
            "Choose stores to compare",
            options=["Aldi", "Farmfoods"],
            default=["Aldi", "Farmfoods"]
        )

        location = st.text_input(
            "Your location",
            placeholder="e.g. Wigan"
        )

        budget = st.number_input(
            "Budget (£)",
            min_value=0.0,
            value=100.0,
            step=1.0
        )

    st.markdown("### Shopping Items")
    raw_items = st.text_area(
        "Enter one item per line",
        placeholder="eggs\nmilk\nbread\nchicken\nrice",
        height=250
    )

    process_clicked = st.button("Process shopping list", type="primary")

    if process_clicked:
        parsed_items = parse_items(raw_items)

        if not parsed_items:
            st.warning("Please enter at least one shopping item.")
            return

        if not selected_stores:
            st.warning("Please choose at least one store.")
            return

        st.session_state.parsed_items = parsed_items
        st.session_state.selected_stores = selected_stores
        st.session_state.location = location.strip()
        st.session_state.budget = budget

        st.success("Shopping list processed successfully.")

    if st.session_state.parsed_items:
        col1, col2 = st.columns([2, 1])

        with col1:
            st.markdown("### Cleaned Shopping List")
            items_df = pd.DataFrame({
                "Wanted Item": st.session_state.parsed_items
            })
            st.dataframe(items_df, use_container_width=True, hide_index=True)

        with col2:
            st.markdown("### Shopping Summary")
            st.metric("Items entered", len(st.session_state.parsed_items))
            st.metric("Budget", f"£{st.session_state.budget:.2f}")
            st.write("**Stores selected:**")
            st.write(", ".join(st.session_state.selected_stores))

            if st.session_state.location:
                st.write(f"**Location:** {st.session_state.location}")
            else:
                st.write("**Location:** Not provided")

        st.markdown("### Next Step")
        st.info(
            "Next, we will search the stores and show comparison results for each item."
        )


if __name__ == "__main__":
    main()
