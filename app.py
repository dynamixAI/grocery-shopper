import streamlit as st
import pandas as pd
import random


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
        {"branch": "Aldi Wigan Central", "address": "Wallgate, Wigan, WN1 1BE", "distance_miles": 0.8},
        {"branch": "Aldi Robin Park", "address": "Scot Lane, Wigan, WN5 0UH", "distance_miles": 1.6},
        {"branch": "Aldi Hindley", "address": "Atherton Road, Hindley, WN2 3EU", "distance_miles": 3.2}
    ],
    "Farmfoods": [
        {"branch": "Farmfoods Wigan", "address": "Standishgate, Wigan, WN1 1UP", "distance_miles": 0.9},
        {"branch": "Farmfoods Ince", "address": "Ince Green Lane, Wigan, WN2 2AL", "distance_miles": 2.4}
    ],
    "Lidl": [
        {"branch": "Lidl Wigan", "address": "Warrington Road, Wigan, WN3 6XB", "distance_miles": 1.4},
        {"branch": "Lidl Pemberton", "address": "Ormskirk Road, Wigan, WN5 9AN", "distance_miles": 2.7}
    ],
    "Asda": [
        {"branch": "Asda Robin Park", "address": "Loire Drive, Wigan, WN5 0UH", "distance_miles": 1.5},
        {"branch": "Asda Golborne", "address": "Atherleigh Way, Golborne, WA3 3SP", "distance_miles": 4.6}
    ],
    "Sainsbury's": [
        {"branch": "Sainsbury's Wigan", "address": "Worthington Way, Wigan, WN3 6XA", "distance_miles": 1.3},
        {"branch": "Sainsbury's Leigh", "address": "The Loom, Leigh, WN7 4XU", "distance_miles": 5.2}
    ]
}


PACK_SIZES = ["500g", "1kg", "2L", "6 pack", "12 pack", "750ml", "1 loaf", "4 rolls"]
OFFERS = ["No offer", "2 for £3", "Club deal", "Special offer", "Reduced today", "Buy 1 Get 1 Half Price"]


def clean_item_text(text: str) -> str:
    return " ".join(text.strip().split())


def initialise_session() -> None:
    defaults = {
        "draft_items": [],
        "confirmed_items": [],
        "selected_store_brands": [],
        "location_input": "",
        "radius_miles": 2,
        "budget": 0.0,
        "nearby_store_results": [],
        "confirmed_stores": [],
        "comparison_results": {},
        "final_selections": {}
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def add_draft_item() -> None:
    raw_value = st.session_state.get("item_input_box", "")
    cleaned_value = clean_item_text(raw_value)

    if not cleaned_value:
        return

    existing_lower = [item.lower() for item in st.session_state.draft_items]
    if cleaned_value.lower() not in existing_lower:
        st.session_state.draft_items.append(cleaned_value)

    st.session_state.item_input_box = ""


def remove_draft_item(index: int) -> None:
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


def generate_mock_product_results(items: list[str], confirmed_stores: list[dict]) -> dict:
    random.seed(42)
    results = {}

    for item in items:
        item_results = []

        for store in confirmed_stores:
            base_price = round(random.uniform(0.79, 6.99), 2)
            pack_size = random.choice(PACK_SIZES)
            offer = random.choice(OFFERS)

            item_results.append({
                "wanted_item": item,
                "store_brand": store["store_brand"],
                "branch": store["branch"],
                "address": store["address"],
                "matched_product": f"{item.title()} - {store['store_brand']} Choice",
                "price": base_price,
                "pack_size": pack_size,
                "offer": offer
            })

        results[item] = item_results

    return results


def main() -> None:
    initialise_session()

    st.title("🛒 Grocery Shopper")
    st.subheader("Precision shopping planner")
    st.write(
        "Enter your items, choose store brands, confirm nearby branches, compare products, and build your basket."
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
            st.session_state.comparison_results = {}
            st.session_state.final_selections = {}

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
        st.session_state.comparison_results = {}
        st.session_state.final_selections = {}

        st.success("Nearby store search completed.")

    if st.session_state.confirmed_items:
        col1, col2 = st.columns([2, 1])

        with col1:
            st.markdown("### Confirmed Shopping List")
            items_df = pd.DataFrame({"Wanted Item": st.session_state.confirmed_items})
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

        nearby_df = pd.DataFrame(st.session_state.nearby_store_results).rename(columns={
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
                st.session_state.comparison_results = {}
                st.session_state.final_selections = {}
                st.success("Store branches confirmed successfully.")

    if st.session_state.confirmed_stores:
        st.markdown("### Confirmed Stores")

        confirmed_df = pd.DataFrame(st.session_state.confirmed_stores).rename(columns={
            "store_brand": "Store",
            "branch": "Branch",
            "address": "Address",
            "distance_miles": "Distance (miles)"
        })
        st.dataframe(confirmed_df, use_container_width=True, hide_index=True)

        if st.button("Compare product prices", type="primary"):
            st.session_state.comparison_results = generate_mock_product_results(
                st.session_state.confirmed_items,
                st.session_state.confirmed_stores
            )
            st.success("Product comparison results generated.")

    if st.session_state.comparison_results:
        st.markdown("## Product Comparison")

        final_selections = {}

        for item, item_results in st.session_state.comparison_results.items():
            st.markdown(f"### {item.title()}")

            item_df = pd.DataFrame(item_results)
            display_df = item_df.rename(columns={
                "store_brand": "Store",
                "branch": "Branch",
                "matched_product": "Matched Product",
                "price": "Price (£)",
                "pack_size": "Pack Size",
                "offer": "Offer"
            })[["Store", "Branch", "Matched Product", "Price (£)", "Pack Size", "Offer"]]

            st.dataframe(display_df, use_container_width=True, hide_index=True)

            selection_options = [
                f"{row['store_brand']} | {row['branch']} | {row['matched_product']} | £{row['price']:.2f} | {row['offer']}"
                for row in item_results
            ]

            selected_option = st.radio(
                f"Choose your preferred option for {item}",
                options=selection_options,
                key=f"selection_{item}"
            )

            selected_index = selection_options.index(selected_option)
            final_selections[item] = item_results[selected_index]

        if st.button("Build final basket", type="primary"):
            st.session_state.final_selections = final_selections
            st.success("Final basket created successfully.")

    if st.session_state.final_selections:
        st.markdown("## Final Basket")

        basket_rows = list(st.session_state.final_selections.values())
        basket_df = pd.DataFrame(basket_rows)

        display_basket_df = basket_df.rename(columns={
            "wanted_item": "Wanted Item",
            "store_brand": "Store",
            "branch": "Branch",
            "matched_product": "Selected Product",
            "price": "Price (£)",
            "pack_size": "Pack Size",
            "offer": "Offer"
        })[["Wanted Item", "Store", "Branch", "Selected Product", "Price (£)", "Pack Size", "Offer"]]

        st.dataframe(display_basket_df, use_container_width=True, hide_index=True)

        total_cost = basket_df["price"].sum()
        budget = st.session_state.budget
        difference = budget - total_cost

        st.markdown("### Basket Summary")
        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Total Basket Cost", f"£{total_cost:.2f}")

        with col2:
            if difference >= 0:
                st.metric("Budget Remaining", f"£{difference:.2f}")
            else:
                st.metric("Over Budget", f"£{abs(difference):.2f}")

        with col3:
            st.metric("Items Selected", len(basket_rows))

        st.markdown("### Spend by Store")
        store_summary = (
            basket_df.groupby("store_brand", as_index=False)["price"]
            .sum()
            .rename(columns={"store_brand": "Store", "price": "Subtotal (£)"})
        )
        st.dataframe(store_summary, use_container_width=True, hide_index=True)


if __name__ == "__main__":
    main()
