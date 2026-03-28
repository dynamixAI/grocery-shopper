import streamlit as st
import pandas as pd


st.set_page_config(
    page_title="Grocery Shopper",
    page_icon="🛒",
    layout="wide"
)


AVAILABLE_STORES = [
    "Aldi",
    "Farmfoods",
    "Lidl",
    "Asda",
    "Sainsbury's"
]


MOCK_STORE_RESULTS = {
    "Aldi": [
        {
            "branch": "Aldi Wigan Central",
            "address": "Wallgate, Wigan, WN1 1BE",
            "distance_miles": 0.8
        },
        {
            "branch": "Aldi Robin Park",
            "address": "Scot Lane, Wigan, WN5 0UH",
            "distance_miles": 1.6
        },
        {
            "branch": "Aldi Hindley",
            "address": "Atherton Road, Hindley, WN2 3EU",
            "distance_miles": 3.2
        }
    ],
    "Farmfoods": [
        {
            "branch": "Farmfoods Wigan",
            "address": "Standishgate, Wigan, WN1 1UP",
            "distance_miles": 0.9
        },
        {
            "branch": "Farmfoods Ince",
            "address": "Ince Green Lane, Wigan, WN2 2AL",
            "distance_miles": 2.4
        }
    ],
    "Lidl": [
        {
            "branch": "Lidl Wigan",
            "address": "Warrington Road, Wigan, WN3 6XB",
            "distance_miles": 1.4
        },
        {
            "branch": "Lidl Pemberton",
            "address": "Ormskirk Road, Wigan, WN5 9AN",
            "distance_miles": 2.7
        }
    ],
    "Asda": [
        {
            "branch": "Asda Robin Park",
            "address": "Loire Drive, Wigan, WN5 0UH",
            "distance_miles": 1.5
        },
        {
            "branch": "Asda Golborne",
            "address": "Atherleigh Way, Golborne, WA3 3SP",
            "distance_miles": 4.6
        }
    ],
    "Sainsbury's": [
        {
            "branch": "Sainsbury's Wigan",
            "address": "Worthington Way, Wigan, WN3 6XA",
            "distance_miles": 1.3
        },
        {
            "branch": "Sainsbury's Leigh",
            "address": "The Loom, Leigh, WN7 4XU",
            "distance_miles": 5.2
        }
    ]
}


def clean_item_text(text: str) -> str:
    """Trim spaces and normalise repeated internal spaces."""
    return " ".join(text.strip().split())


def initialise_session() -> None:
    if "draft_items" not in st.session_state:
        st.session_state.draft_items = []

    if "confirmed_items" not in st.session_state:
        st.session_state.confirmed_items = []

    if "selected_store_brands" not in st.session_state:
        st.session_state.selected_store_brands = []

    if "location_input" not in st.session_state:
        st.session_state.location_input = ""

    if "radius_miles" not in st.session_state:
        st.session_state.radius_miles = 2

    if "budget" not in st.session_state:
        st.session_state.budget = 0.0

    if "nearby_store_results" not in st.session_state:
        st.session_state.nearby_store_results = []

    if "confirmed_stores" not in st.session_state:
        st.session_state.confirmed_stores = []


def add_draft_item() -> None:
    """Add item from the slim input box into the draft list."""
    raw_value = st.session_state.get("item_input_box", "")
    cleaned_value = clean_item_text(raw_value)

    if not cleaned_value:
        return

    existing_lower = [item.lower() for item in st.session_state.draft_items]
    if cleaned_value.lower() not in existing_lower:
        st.session_state.draft_items.append(cleaned_value)

    st.session_state.item_input_box = ""


def remove_draft_item(index: int) -> None:
    """Remove a draft item by index."""
    if 0 <= index < len(st.session_state.draft_items):
        st.session_state.draft_items.pop(index)


def get_mock_nearby_stores(selected_brands: list[str], radius_miles: int) -> list[dict]:
    results = []

    for brand in selected_brands:
        store_list = MOCK_STORE_RESULTS.get(brand, [])

        for store in store_list:
            if store["distance_miles"] <= radius_miles:
                results.append({
                    "store_brand": brand,
                    "branch": store["branch"],
                    "address": store["address"],
                    "distance_miles": store["distance_miles"]
                })

    results.sort(key=lambda x: x["distance_miles"])
    return results


def main() -> None:
    initialise_session()

    st.title("🛒 Grocery Shopper")
    st.subheader("Precision shopping planner")
    st.write(
        "Enter your items, choose store brands, search nearby branches, and confirm the exact stores you want to compare."
    )

    with st.sidebar:
        st.header("Shopping Settings")

        selected_store_brands = st.multiselect(
            "Choose store brands to search",
            options=AVAILABLE_STORES,
            default=[]
        )

        location_input = st.text_input(
            "Postcode or area",
            placeholder="e.g. WN1 3FG or Wigan"
        )

        radius_miles = st.slider(
            "Search radius (miles)",
            min_value=1,
            max_value=10,
            value=2,
            step=1
        )

        budget = st.number_input(
            "Budget (£)",
            min_value=0.0,
            value=100.0,
            step=1.0
        )

    st.markdown("### Shopping Items")
    st.text_input(
        "Type one item and press Enter",
        key="item_input_box",
        placeholder="e.g. milk",
        on_change=add_draft_item
    )

    col_a, col_b = st.columns([1, 1])

    with col_a:
        if st.button("Add item"):
            add_draft_item()

    with col_b:
        if st.button("Clear draft list"):
            st.session_state.draft_items = []
            st.session_state.confirmed_items = []
            st.session_state.nearby_store_results = []
            st.session_state.confirmed_stores = []

    if st.session_state.draft_items:
        st.markdown("### Current Item List")

        for idx, item in enumerate(st.session_state.draft_items):
            item_col, remove_col = st.columns([5, 1])

            with item_col:
                st.write(f"• {item}")

            with remove_col:
                if st.button("Remove", key=f"remove_item_{idx}"):
                    remove_draft_item(idx)
                    st.rerun()

        if st.button("Done", type="primary"):
            st.session_state.confirmed_items = st.session_state.draft_items.copy()
            st.success("Shopping list confirmed.")

    process_clicked = st.button("Find nearby stores")

    if process_clicked:
        parsed_items = st.session_state.confirmed_items

        if not parsed_items:
            st.warning("Please add your items and click Done first.")
            return

        if not selected_store_brands:
            st.warning("Please choose at least one store brand.")
            return

        if not location_input.strip():
            st.warning("Please enter a postcode or area.")
            return

        nearby_store_results = get_mock_nearby_stores(selected_store_brands, radius_miles)

        st.session_state.selected_store_brands = selected_store_brands
        st.session_state.location_input = location_input.strip()
        st.session_state.radius_miles = radius_miles
        st.session_state.budget = budget
        st.session_state.nearby_store_results = nearby_store_results
        st.session_state.confirmed_stores = []

        st.success("Nearby store search completed.")

    if st.session_state.confirmed_items:
        col1, col2 = st.columns([2, 1])

        with col1:
            st.markdown("### Confirmed Shopping List")
            items_df = pd.DataFrame({
                "Wanted Item": st.session_state.confirmed_items
            })
            st.dataframe(items_df, use_container_width=True, hide_index=True)

        with col2:
            st.markdown("### Shopping Summary")
            st.metric("Items entered", len(st.session_state.confirmed_items))
            st.metric("Budget", f"£{st.session_state.budget:.2f}")
            st.metric("Radius", f"{st.session_state.radius_miles} mile(s)")

            if st.session_state.location_input:
                st.write("**Location input:**")
                st.write(st.session_state.location_input)

            if st.session_state.selected_store_brands:
                st.write("**Store brands selected:**")
                st.write(", ".join(st.session_state.selected_store_brands))

    if st.session_state.nearby_store_results:
        st.markdown("### Nearby Stores Found")

        nearby_df = pd.DataFrame(st.session_state.nearby_store_results)
        nearby_df = nearby_df.rename(columns={
            "store_brand": "Store",
            "branch": "Branch",
            "address": "Address",
            "distance_miles": "Distance (miles)"
        })
        st.dataframe(nearby_df, use_container_width=True, hide_index=True)

        st.markdown("### Confirm Exact Stores")
        st.write("Tick the branches you want to use for product comparison.")

        confirmed_stores = []

        for idx, store in enumerate(st.session_state.nearby_store_results):
            label = (
                f"{store['store_brand']} — {store['branch']} | "
                f"{store['address']} | {store['distance_miles']} miles"
            )

            is_selected = st.checkbox(label, key=f"store_checkbox_{idx}")

            if is_selected:
                confirmed_stores.append(store)

        if st.button("Confirm selected stores"):
            if not confirmed_stores:
                st.warning("Please tick at least one store branch to continue.")
            else:
                st.session_state.confirmed_stores = confirmed_stores
                st.success("Store branches confirmed successfully.")

    if st.session_state.confirmed_stores:
        st.markdown("### Confirmed Stores")

        confirmed_df = pd.DataFrame(st.session_state.confirmed_stores)
        confirmed_df = confirmed_df.rename(columns={
            "store_brand": "Store",
            "branch": "Branch",
            "address": "Address",
            "distance_miles": "Distance (miles)"
        })
        st.dataframe(confirmed_df, use_container_width=True, hide_index=True)

        st.info(
            "Next, we will search products only from these confirmed store branches and compare prices."
        )


if __name__ == "__main__":
    main()
