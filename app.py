import random
import streamlit as st
import plotly.graph_objects as go
import textwrap
import uuid

# ──────────────────────────────────────────────────────────────────────────────
# 0. PAGE CONFIG & THEME
# ──────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Lunch Spinner 3000",
    page_icon="🍕",
    layout="wide",
    initial_sidebar_state="expanded"
)

PALETTE = [
    "#EF476F",  # Vivid Pink
    "#FFD166",  # Bright Gold
    "#06D6A0",  # Teal Green
    "#118AB2",  # Bold Sky Blue
    "#073B4C",  # Deep Navy
    "#FF6B6B",  # Coral Red
    "#4ECDC4",  # Turquoise
    "#1A535C",  # Dark Teal
]
SLICE_TEXT_COLOR = "#FFFFFF"  # White text still works with these


# ──────────────────────────────────────────────────────────────────────────────
# 1.  CONFIGURE YOUR RESTAURANTS & MENU PICKS HERE
# ──────────────────────────────────────────────────────────────────────────────
DEFAULT_FOOD_CHOICES = {
    "Chipotle": ["Sofritas burrito", "Sofritas bowl"],
    "Rosa's Pizza": ["Grandma slice", "Margherita slice", "Garlic knots"],
    "Best Pizza": ["Grandma slice", "White slice", "Garlic knots"],
    "Halal Munchies": ["Mixed platter over rice", "Wings"],
    "Gunther’s": ["Grilled cheese", "Tomato soup"],
    "Subway": ["Tuna 12” sandwich"],
    "Salty Little Lady Luncheonette": ["Tuna crunch sandwich"],
    "La Casita Mexicana": ["Fish tacos", "Guac & chips"],
    "Pattanian Thai": ["Chicken Drunken Noodles"],
    "BK Jani": ["Jani Burger", "Lamb Chops", "Fries"],
    "Namkeen": ["Chicken sandwich", "Tikka melt", "Chicken Tender"],
    "Blue Hour": ["Burger"],
    "Zatar": ["Mediterranean bowl"],
    "Peri Peri Flamin Grill": ["Half spicy chicken"],
    "Eat Real Halal": ["Mixed over rice gyro"],
    "Karachi Kabab Boiz": ["Behari kebab roll", "Malai chicken roll"],
    "McDonald’s": ["Filet-O-Fish"],
}

# ──────────────────────────────────────────────────────────────────────────────
# SETUP SESSION STATE
# ──────────────────────────────────────────────────────────────────────────────
if "food_dict" not in st.session_state:
    st.session_state.food_dict = DEFAULT_FOOD_CHOICES.copy()
if "last_pick" not in st.session_state:
    st.session_state.last_pick = None

# Unique key for Plotly chart to handle updates properly
PLOTLY_CHART_KEY = "food_wheel_chart_" + str(uuid.uuid4())

def calculate_initial_rotation(food_dictionary):
    num_s = len(food_dictionary)
    if num_s < 1: num_s = 1 # Avoid division by zero
    slice_angle = 360 / num_s
    return (90 - (0.5 * slice_angle)) % 360

initial_rotation_val = calculate_initial_rotation(st.session_state.get("food_dict", DEFAULT_FOOD_CHOICES))

if "current_pie_rotation_for_python_render" not in st.session_state:
    st.session_state.current_pie_rotation_for_python_render = initial_rotation_val
if "cumulative_rotation_tracker" not in st.session_state:
    st.session_state.cumulative_rotation_tracker = initial_rotation_val

# ──────────────────────────────────────────────────────────────────────────────
# UTILITY FUNCTIONS & CONSTANTS
# ──────────────────────────────────────────────────────────────────────────────
WRAP_LABELS = True
MAX_LABEL_WIDTH = 12
MAX_LABEL_LINES = 2

def get_display_labels(names):
    if WRAP_LABELS:
        wrapped_labels = []
        for name in names:
            lines = textwrap.wrap(name, width=MAX_LABEL_WIDTH, max_lines=MAX_LABEL_LINES, placeholder="…")
            wrapped_labels.append("<br>".join(lines))
        return wrapped_labels
    return names

def build_initial_wheel_figure(rotation_angle_for_pie, labels_for_pie, current_colors):
    pie_trace = go.Pie(
        labels=labels_for_pie,
        values=[1] * len(labels_for_pie),
        hole=0.35,
        marker=dict(
            colors=current_colors,
            line=dict(color="#FFFFFF", width=3)
        ),
        sort=False,
        direction="clockwise",
        rotation=rotation_angle_for_pie,
        textinfo="label",
        textposition="inside",
        insidetextorientation="radial",
        textfont=dict(size=11, color=SLICE_TEXT_COLOR, family="Arial, sans-serif"),
        hoverinfo="label",
    )
    
    layout = go.Layout(
        showlegend=False,
        margin=dict(l=10, r=10, t=25, b=10), # Keep reduced margins
        height=490, # DESKTOP/MOBILE COMPROMISE: Increased from 420, decreased from 550
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Arial, sans-serif", size=12, color="#333333"),
        annotations=[
            go.layout.Annotation(
                x=0.5, y=0.56, xref='paper', yref='paper', # Arrowhead position
                ax=0.5, ay=0.66, axref='x domain', ayref='y domain', # Arrow tail position
                showarrow=True, arrowcolor="#1E2A38", arrowwidth=3, arrowhead=2, arrowsize=1.3, text="",
            )
        ]
    )
    fig = go.Figure(data=[pie_trace], layout=layout)
    # autosize=True is generally good. If height is specified, it will respect height
    # and autosize width when use_container_width=True in st.plotly_chart.
    fig.update_layout(autosize=True)
    return fig

# ──────────────────────────────────────────────────────────────────────────────
# SIDEBAR - Configuration Panel
# ──────────────────────────────────────────────────────────────────────────────
st.sidebar.header("🛠️ Configure Wheel")
st.sidebar.markdown("---")

with st.sidebar.expander("➕ Add / Update Restaurant", expanded=False):
    with st.form(key="add_restaurant_form", clear_on_submit=True):
        new_name = st.text_input("Restaurant Name", placeholder="e.g., The Pizza Place")
        new_items_str = st.text_area("Menu Items (one per line)", placeholder="e.g., Pepperoni Slice\nGarlic Knots")
        submitted = st.form_submit_button("💾 Save Restaurant", type="primary", use_container_width=True)
        
        if submitted:
            if not new_name.strip():
                st.warning("Restaurant name cannot be empty.")
            else:
                items = [i.strip() for i in new_items_str.splitlines() if i.strip()]
                if not items:
                    st.warning("Please add at least one menu item.")
                else:
                    st.session_state.food_dict[new_name.strip()] = items
                    st.success(f"'{new_name.strip()}' saved successfully!")
                    new_initial_rot = calculate_initial_rotation(st.session_state.food_dict)
                    st.session_state.current_pie_rotation_for_python_render = new_initial_rot
                    st.session_state.cumulative_rotation_tracker = new_initial_rot
                    st.session_state.last_pick = None
                    st.rerun()

st.sidebar.markdown("---")
if st.sidebar.button("🔄 Reset to Defaults", key="reset_defaults_button_sidebar", use_container_width=True):
    st.session_state.food_dict = DEFAULT_FOOD_CHOICES.copy()
    reset_initial_rot = calculate_initial_rotation(st.session_state.food_dict)
    st.session_state.current_pie_rotation_for_python_render = reset_initial_rot
    st.session_state.cumulative_rotation_tracker = reset_initial_rot
    st.session_state.last_pick = None
    st.sidebar.success("🎡 Wheel reset to default restaurants!")
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.markdown("⚙️ **Current Restaurants**")
if not st.session_state.food_dict:
    st.sidebar.info("No restaurants configured. Add some to spin!")
else:
    restaurants_to_delete = []
    for r_name_loop_var in list(st.session_state.food_dict.keys()):
        col1, col2 = st.sidebar.columns([0.85, 0.15], gap="small")
        with col1:
            with st.expander(f"**{r_name_loop_var}** ({len(st.session_state.food_dict.get(r_name_loop_var, []))} items)"):
                for item in st.session_state.food_dict.get(r_name_loop_var, []):
                    st.markdown(f"- {item}")
        with col2:
            del_key = f"del_btn_{r_name_loop_var.replace(' ','_')}_{str(uuid.uuid4())[:4]}"
            if st.button("🗑️", key=del_key, help=f"Delete {r_name_loop_var}", use_container_width=True):
                restaurants_to_delete.append(r_name_loop_var)
    
    if restaurants_to_delete:
        for r_name_to_del in restaurants_to_delete:
            if r_name_to_del in st.session_state.food_dict:
                del st.session_state.food_dict[r_name_to_del]
        st.session_state.last_pick = None 
        if st.session_state.food_dict :
             new_initial_rot = calculate_initial_rotation(st.session_state.food_dict)
        else:
            new_initial_rot = 90 
        st.session_state.current_pie_rotation_for_python_render = new_initial_rot
        st.session_state.cumulative_rotation_tracker = new_initial_rot
        st.rerun()
st.sidebar.markdown("---")
st.sidebar.caption("Made with ❤️ using Streamlit & Plotly.")


# ──────────────────────────────────────────────────────────────────────────────
# MAIN PAGE - The Wheel and Results
# ──────────────────────────────────────────────────────────────────────────────
st.markdown("<h1 style='text-align: center; color: #1B4332;'>🥡 What's for Lunch? Spin the Wheel! 🥡</h1>", unsafe_allow_html=True)
st.markdown("---")

food_names_original = list(st.session_state.food_dict.keys())
num_slices = len(food_names_original)

if num_slices == 0 :
    st.error("🚨 No restaurants configured! Please add some via the sidebar to spin the wheel.")
    st.stop()
elif num_slices == 1:
    st.warning("⚠️ Only one restaurant configured. Add at least one more to spin the wheel!")

food_names_display = get_display_labels(food_names_original)
current_colors = [PALETTE[i % len(PALETTE)] for i in range(num_slices)]
slice_angle_degrees = 360 / num_slices if num_slices > 0 else 360

main_col1, main_col2 = st.columns([0.6, 0.4], gap="large")

with main_col1:
    # Removed st.markdown("####") for tighter spacing, good for mobile
    if num_slices > 0:
        figure_to_display = build_initial_wheel_figure(
            st.session_state.current_pie_rotation_for_python_render,
            food_names_display,
            current_colors
        )
        st.plotly_chart(figure_to_display, use_container_width=True, key=PLOTLY_CHART_KEY)
    else:
        st.info("Add restaurants to see the wheel.")


with main_col2:
    # Removed st.markdown("##") for tighter spacing, good for mobile
    if num_slices < 2:
        st.info("ℹ️ Add at least two restaurants to enable spinning.")
    else:
        if st.button("🎯 Spin the Wheel! 🎯", key="spin_button_main", use_container_width=True, type="primary", help="Click to find out your culinary fate!"):
            chosen_index = random.randrange(num_slices)
            st.session_state.last_pick = food_names_original[chosen_index]

            target_visual_resting_angle_0_360 = (90 - (chosen_index * slice_angle_degrees) - (slice_angle_degrees / 2)) % 360
            num_extra_full_rotations_for_jump_effect = random.randint(4, 7) 
            current_cumulative = st.session_state.cumulative_rotation_tracker
            current_visual_0_360 = current_cumulative % 360
            angular_travel_to_resting_spot = (target_visual_resting_angle_0_360 - current_visual_0_360 + 360) % 360
            new_rotation_for_plotly_jump = current_cumulative + angular_travel_to_resting_spot + (num_extra_full_rotations_for_jump_effect * 360)

            st.session_state.current_pie_rotation_for_python_render = new_rotation_for_plotly_jump
            st.session_state.cumulative_rotation_tracker = new_rotation_for_plotly_jump
            st.rerun()

    st.markdown("---")

    if st.session_state.last_pick:
        st.markdown(f"<h2 style='text-align: center; color: #D00000;'>🎉 Today's Delicious Pick! 🎉</h2>", unsafe_allow_html=True)
        st.markdown(f"<p style='font-size: 28px; font-weight: bold; text-align: center; margin-bottom: 20px;'>{st.session_state.last_pick}</p>", unsafe_allow_html=True)
        
        st.markdown("#### 📜 **Menu Suggestions:**")
        if st.session_state.last_pick in st.session_state.food_dict:
            menu_items = st.session_state.food_dict[st.session_state.last_pick]
            if menu_items:
                items_html = "".join([f"<p style='font-size: 17px; margin-bottom: 5px; color: #333;'>• {item}</p>" for item in menu_items])
                st.markdown(
                    f"""
                    <div style="
                        border: 1.5px solid #e0e0e0;
                        border-radius: 8px;
                        padding: 15px 20px;
                        background-color: #f9f9f9;
                        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
                    ">
                    {items_html}
                    </div>
                    """, unsafe_allow_html=True
                )
            else:
                st.info("🗒️ No specific menu items listed for this restaurant.")
        else:
            st.warning(f"🤷 Details for '{st.session_state.last_pick}' not found. This might be due to a recent deletion.")
        
        st.markdown("---")
        if st.button("🧹 Clear Pick & Spin Again?", key="clear_pick_button", use_container_width=True):
            st.session_state.last_pick = None
            st.rerun()
    elif num_slices >=2:
        st.info("✨ Spin the wheel to discover your next meal! ✨")
    elif num_slices == 1:
        st.info(f"✨ Your only option is: **{food_names_original[0]}**! Add more to spin. ✨")


st.markdown("<br><br>", unsafe_allow_html=True)
