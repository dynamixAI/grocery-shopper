import streamlit as st
import pandas as pd
import random

from services.geocoding import geocode_location, GeocodingError

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
        "step": 1,
        "draft_items": [],
        "confirmed_items": [],
        "location_input": "",
        "radius_miles": 2,
        "budget": 100.0,
        "selected_store_brands": [],
        "nearby_store_results": [],
        "confirmed_stores": [],
        "comparison_results": {},
        "final_selections": {},
        "shopping_checklist": {}
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def go_to_step(step_number: int) -> None:
    st.session_state.step = step_number


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


def render_progress() -> None:
    st.progress(st.session_state.step / 6)


def step_1_items() -> None:
    st.markdown("## Add Shopping Items")

    st.text_input(
        "Type one item and press Enter",
        key="item_input_box",
        placeholder="e.g. milk",
        on_change=add_draft_item
    )

    col1, col2 = st.columns(2)

    with col1:
        if st.button("Add item"):
            add_draft_item()

    with col2:
        if st.button("Clear item list"):
            st.session_state.draft_items = []
            st.session_state.confirmed_items = []
            st.rerun()

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

    if st.session_state.confirmed_items:
        st.markdown("### Confirmed Shopping List")
        items_df = pd.DataFrame({"Wanted Item": st.session_state.confirmed_items})
        st.dataframe(items_df, use_container_width=True, hide_index=True)

        if st.button("Next →"):
            go_to_step(2)
            st.rerun()


def step_2_location_budget() -> None:
    st.markdown("## Location and Budget")

    st.text_input(
        "Postcode or area",
        key="location_input",
        placeholder="e.g. WN1 3FG or Wigan"
    )

    if st.button("Test location lookup"):
        try:
            query = st.session_state.location_input.strip()
            result = geocode_location(query)

            if not query:
                st.warning("Please enter a postcode or area first.")
            elif result is None:
                st.warning("No location match found.")
            else:
                st.success("Location found successfully.")
                st.write(f"**Matched location:** {result['display_name']}")
                st.write(f"**Latitude:** {result['lat']}")
                st.write(f"**Longitude:** {result['lon']}")

        except GeocodingError as exc:
            st.error(str(exc))

    st.slider(
        "Search radius (miles)",
        min_value=1,
        max_value=10,
        step=1,
        key="radius_miles"
    )

    st.number_input(
        "Budget (£)",
        min_value=0.0,
        step=1.0,
        key="budget"
    )

    col1, col2 = st.columns(2)

    with col1:
        if st.button("← Back"):
            go_to_step(1)
            st.rerun()

    with col2:
        if st.button("Next →", type="primary"):
            if not st.session_state.location_input.strip():
                st.warning("Please enter a postcode or area.")
            else:
                go_to_step(3)
                st.rerun()


def step_3_stores() -> None:
    st.markdown("## Stores")

    selected_store_brands = st.multiselect(
        "Choose store brands to search",
        options=AVAILABLE_STORES,
        default=st.session_state.selected_store_brands
    )

    if st.button("Find nearby stores", type="primary"):
        if not selected_store_brands:
            st.warning("Please choose at least one store brand.")
        else:
            st.session_state.selected_store_brands = selected_store_brands
            st.session_state.nearby_store_results = get_mock_nearby_stores(
                selected_store_brands,
                st.session_state.radius_miles
            )
            st.session_state.confirmed_stores = []
            st.session_state.comparison_results = {}
            st.session_state.final_selections = {}
            st.session_state.shopping_checklist = {}

            for key in list(st.session_state.keys()):
                if key.startswith("store_checkbox_"):
                    del st.session_state[key]

            st.success("Nearby store search completed.")
            st.rerun()

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

        for idx, store in enumerate(st.session_state.nearby_store_results):
            label = (
                f"{store['store_brand']} — {store['branch']} | "
                f"{store['address']} | {store['distance_miles']} miles"
            )
            st.checkbox(label, key=f"store_checkbox_{idx}")

        if st.button("Confirm selected stores"):
            confirmed_stores = []

            for idx, store in enumerate(st.session_state.nearby_store_results):
                if st.session_state.get(f"store_checkbox_{idx}", False):
                    confirmed_stores.append(store)

            if not confirmed_stores:
                st.warning("Please tick at least one store branch.")
            else:
                st.session_state.confirmed_stores = confirmed_stores
                st.success("Store branches confirmed successfully.")
                st.rerun()

    if st.session_state.confirmed_stores:
        st.markdown("### Confirmed Stores")
        confirmed_df = pd.DataFrame(st.session_state.confirmed_stores).rename(columns={
            "store_brand": "Store",
            "branch": "Branch",
            "address": "Address",
            "distance_miles": "Distance (miles)"
        })
        st.dataframe(confirmed_df, use_container_width=True, hide_index=True)

    col1, col2 = st.columns(2)

    with col1:
        if st.button("← Back"):
            go_to_step(2)
            st.rerun()

    with col2:
        if st.button("Next →", type="primary"):
            if not st.session_state.confirmed_stores:
                st.warning("Please confirm at least one store branch.")
            else:
                go_to_step(4)
                st.rerun()


def step_4_compare() -> None:
    st.markdown("## Compare Products")

    if not st.session_state.comparison_results:
        if st.button("Generate product comparison", type="primary"):
            st.session_state.comparison_results = generate_mock_product_results(
                st.session_state.confirmed_items,
                st.session_state.confirmed_stores
            )
            st.success("Product comparison results generated.")
            st.rerun()

    if st.session_state.comparison_results:
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

        if st.button("Save selections", type="primary"):
            st.session_state.final_selections = final_selections
            st.session_state.shopping_checklist = {
                item: False for item in final_selections.keys()
            }
            st.success("Selections saved.")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("← Back"):
            go_to_step(3)
            st.rerun()

    with col2:
        if st.button("Next →", type="primary"):
            if not st.session_state.final_selections:
                st.warning("Please save your product selections first.")
            else:
                go_to_step(5)
                st.rerun()


def step_5_basket() -> None:
    st.markdown("## Final Basket")

    basket_rows = list(st.session_state.final_selections.values())

    if not basket_rows:
        st.warning("No basket selections found.")
    else:
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

        csv_download_df = basket_df.rename(columns={
            "wanted_item": "wanted_item",
            "store_brand": "store",
            "branch": "branch",
            "matched_product": "selected_product",
            "price": "price_gbp",
            "pack_size": "pack_size",
            "offer": "offer"
        })[["wanted_item", "store", "branch", "selected_product", "price_gbp", "pack_size", "offer"]]

        csv_data = csv_download_df.to_csv(index=False).encode("utf-8")

        st.download_button(
            label="Download basket as CSV",
            data=csv_data,
            file_name="grocery_shopper_final_basket.csv",
            mime="text/csv"
        )

    col1, col2 = st.columns(2)

    with col1:
        if st.button("← Back"):
            go_to_step(4)
            st.rerun()

    with col2:
        if st.button("Start Shopping", type="primary"):
            if not basket_rows:
                st.warning("No basket selections found.")
            else:
                go_to_step(6)
                st.rerun()


def step_6_shopping_list() -> None:
    st.markdown("## Shopping List")
    st.write("Tick items as you place them in your basket.")

    basket_rows = list(st.session_state.final_selections.values())

    if not basket_rows:
        st.warning("No shopping list found.")
    else:
        if not st.session_state.shopping_checklist:
            st.session_state.shopping_checklist = {
                row["wanted_item"]: False for row in basket_rows
            }

        picked_count = 0
        total_items = len(basket_rows)

        for row in basket_rows:
            wanted_item = row["wanted_item"]
            checkbox_key = f"basket_check_{wanted_item}"
            current_value = st.session_state.shopping_checklist.get(wanted_item, False)

            with st.container():
                checked = st.checkbox(
                    f"Pick {wanted_item.title()}",
                    value=current_value,
                    key=checkbox_key
                )

                st.markdown(
                    f"""
**Selected product:** {row['matched_product']}  
**Store:** {row['store_brand']}  
**Branch:** {row['branch']}  
**Price:** £{row['price']:.2f}  
**Pack size:** {row['pack_size']}  
**Offer:** {row['offer']}
"""
                )

                st.divider()

            st.session_state.shopping_checklist[wanted_item] = checked

            if checked:
                picked_count += 1

        remaining_count = total_items - picked_count
        progress_value = picked_count / total_items if total_items > 0 else 0

        st.markdown("### Shopping Progress")
        st.progress(progress_value)

        col1, col2, col3 = st.columns(3)

        with col1:
            st.metric("Picked", picked_count)

        with col2:
            st.metric("Remaining", remaining_count)

        with col3:
            st.metric("Completion", f"{progress_value * 100:.0f}%")

        if picked_count == total_items and total_items > 0:
            st.success("Everything on your list has been picked.")

    if st.button("← Back to Basket"):
        go_to_step(5)
        st.rerun()


def main() -> None:
    initialise_session()

    st.title("🛒 Grocery Shopper")
    st.write("A step-by-step grocery comparison planner.")

    render_progress()

    if st.session_state.step == 1:
        step_1_items()
    elif st.session_state.step == 2:
        step_2_location_budget()
    elif st.session_state.step == 3:
        step_3_stores()
    elif st.session_state.step == 4:
        step_4_compare()
    elif st.session_state.step == 5:
        step_5_basket()
    elif st.session_state.step == 6:
        step_6_shopping_list()


if __name__ == "__main__":
    main()
