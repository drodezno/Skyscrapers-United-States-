import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
import pydeck as pdk

# Color palette
girly_palette = {
    'background': '#FFF0F5',  # Lavender Blush
    'bar_color': '#FFB6C1',  # Light Pink
    'highlight': '#FF69B4',  # Hot Pink
    'text_color': '#8B008B',  # Dark Magenta
    'metric_text': '#FF1493',  # Deep Pink
    'metric_background': '#FFD1DC',  # Pastel Pink
}

# Streamlit CSS with the color palette
st.markdown(
    """
    <style>
    div[data-testid="metric-container"] {
        background-color: """ + girly_palette['metric_background'] + """;
        border: 1px solid """ + girly_palette['highlight'] + """;
        border-radius: 10px;
        padding: 5% 5% 5% 10%;
        color: """ + girly_palette['metric_text'] + """;
        font-weight: bold;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.title("Skyscrapers Around the United States")

## Allowing file upload
@st.cache_data
def load_data(file):
    try:
        # Reads excel file
        data = pd.read_excel(file, engine="openpyxl", header=0)
        summary = (data.shape[0], data.shape[1])  ##Gives general info from data
        return data, summary
    except Exception as e:
        st.error(f"Error loading dataset: {e}")
        st.stop()
        return None, None

## Sidebar file uploader
uploaded_file = st.sidebar.file_uploader("Upload your Excel file", type=["xlsx"])

## load and display data if file provided
if uploaded_file is not None:

    data, data_summary = load_data(uploaded_file)
    if data is not None:
        st.sidebar.write(f"Dataset loaded with {data_summary[0]} rows and {data_summary[1]} columns.")

        ##Check latitude and Longitude is okay
        data = data.dropna(subset=['location.latitude', 'location.longitude'])

        # Extracts height columns
        height_columns = [col for col in data.columns if 'height' in col.lower()]

        # Using height if identified
        if height_columns:
            height_column_name = height_columns[0]
        else:
            st.sidebar.error("No column containing 'height' found!")
            height_column_name = None

        # Add city filter to sidebar
        cities = data['location.city'].unique()
        selected_city = st.sidebar.selectbox("Select a city:", cities)

        # Filter data based on city selection
        filtered_data = data[data['location.city'] == selected_city]

        # Streamlit compatibility: Rename latitude and longitude columns
        filtered_data = filtered_data.rename(columns={
            'location.latitude': 'latitude',
            'location.longitude': 'longitude'
        })

        # sorting options in sidebar
        sort_order = st.sidebar.radio("Sort skyscrapers by height:", ["Ascending", "Descending"])
        ascending = sort_order == "Ascending"  # Convert to boolean

        # Sort filtered data by height
        if height_column_name:
            sorted_data = filtered_data.sort_values(by=height_column_name, ascending=ascending)

            # Rename columns for nicer display
            sorted_data = sorted_data.rename(columns={
                'name': 'Name',
                'location.city': 'Location',
                height_column_name: 'Height'
            })

            # Use only relevant columns
            columns_to_display = ['Name', 'Location', 'Height']

            # Show result table with changes
            st.write(f"Skyscrapers in {selected_city}, sorted by height ({sort_order}):")
            st.write(sorted_data[columns_to_display])
        else:
            sorted_data = filtered_data
            st.warning("Height column not found, skipping sorting.")

        # Group skyscrapers by city and find average height
        if height_column_name:
            city_group = data.groupby('location.city')[height_column_name].mean().reset_index()
            city_group = city_group.rename(columns={
                'location.city': 'Location',
                height_column_name: 'Height'
            })
            st.subheader("Average Height of Skyscrapers by City")
            st.write(city_group)

        #  Animations: Display balloons when data is successfully loaded
        if not filtered_data.empty:
            st.balloons()

        # Key Highlights Section
        st.subheader("Key Highlights")
        if not filtered_data.empty and height_column_name:
            total_skyscrapers = len(filtered_data)
            tallest_skyscraper = filtered_data.loc[filtered_data[height_column_name].idxmax()]
            tallest_name = tallest_skyscraper['name']
            tallest_height = tallest_skyscraper[height_column_name]
            average_height = filtered_data[height_column_name].mean()

            # Styled table using HTML (learned in World Wide Web)
            st.markdown(f"""
            <style>
            .highlights-table {{
                width: 100%;
                border-collapse: collapse;
                margin: 20px 0;
                font-size: 1.1em;
                text-align: left;
            }}
            .highlights-table th, .highlights-table td {{
                border: 1px solid {girly_palette['highlight']};
                padding: 10px;
                background-color: {girly_palette['background']};
                color: {girly_palette['text_color']};
            }}
            .highlights-table th {{
                background-color: {girly_palette['highlight']};
                color: white;
            }}
            </style>

            <table class="highlights-table">
                <thead>
                    <tr>
                        <th>Metric</th>
                        <th>Value</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td>Total Skyscrapers</td>
                        <td>{total_skyscrapers}</td>
                    </tr>
                    <tr>
                        <td>Tallest Skyscraper</td>
                        <td>{tallest_name} ({tallest_height} m)</td>
                    </tr>
                    <tr>
                        <td>Average Skyscraper Height</td>
                        <td>{average_height:.2f} m</td>
                    </tr>
                </tbody>
            </table>
            """, unsafe_allow_html=True)
        else:
            st.warning("No data available for the selected city.")

        #  Height Filtering can be altered by user
        if not filtered_data.empty and height_column_name:
           #Slider based on height
            st.sidebar.subheader("Filter by Height")
            min_height = st.sidebar.slider(
                "Minimum Height (m):",
                min_value=0,
                max_value=int(filtered_data[height_column_name].max()),
                value=100
            )

            # Apply height filter
            filtered_by_height = sorted_data[sorted_data['Height'] >= min_height]

            # Enhanced Map Features - filtered by height
            st.subheader("Enhanced Map of Skyscrapers")
            if not filtered_by_height.empty:
                map_layer = pdk.Layer(
                    'ScatterplotLayer',
                    data=filtered_by_height,
                    get_position=['longitude', 'latitude'],
                    get_color=[255, 105, 180, 160],  ## color was added
                    get_radius=100,
                )
                map_view = pdk.ViewState(
                    latitude=filtered_by_height['latitude'].mean(),
                    longitude=filtered_by_height['longitude'].mean(),
                    zoom=10,
                    pitch=45,
                )
                st.pydeck_chart(pdk.Deck(layers=[map_layer], initial_view_state=map_view))
            else:
                st.warning(f"No skyscrapers with height >= {min_height} meters in {selected_city}.")

            # Display filtered data
            st.header(f"Skyscrapers in {selected_city} with Height >= {min_height} meters")
            if not filtered_by_height.empty:

                with st.expander("Show Filtered Data by Height"):
                    st.write(filtered_by_height)

                # Bar Chart
                st.subheader("Height Distribution of Filtered Skyscrapers")
                fig, ax = plt.subplots(figsize=(8, 5))
                filtered_by_height['Height'].hist(bins=10, ax=ax, color=girly_palette['bar_color'])
                ax.set_title(f"Height Distribution in {selected_city} (Filtered)", color=girly_palette['text_color'], fontsize=16)
                ax.set_xlabel("Height (m)", color=girly_palette['text_color'])
                ax.set_ylabel("Frequency", color=girly_palette['text_color'])
                ax.spines['top'].set_visible(False)
                ax.spines['right'].set_visible(False)
                ax.spines['bottom'].set_color(girly_palette['text_color'])
                ax.spines['left'].set_color(girly_palette['text_color'])
                ax.tick_params(axis='x', colors=girly_palette['text_color'])
                ax.tick_params(axis='y', colors=girly_palette['text_color'])
                st.pyplot(fig)

            # Iterate through rows
            st.subheader("Sample Skyscraper Data")
            for index, row in filtered_by_height.head(5).iterrows():
                st.write(f"{index + 1}. {row['Name']} ({row['Height']} m)")
else:
    st.warning("Please upload a dataset to begin.")

# Pie Chart: Distribution of Skyscrapers by City
if 'data' in locals() and data is not None and not data.empty:
    st.subheader("Distribution of Skyscrapers by City")

    # Group data by 'location.city' find number of skyscrapers per city
    if 'location.city' in data.columns:
        city_skyscraper_count = data['location.city'].value_counts().reset_index()
        city_skyscraper_count.columns = ['City', 'Number of Skyscrapers']

        # Filter for the top 10 cities with the most skyscrapers
        top_cities = city_skyscraper_count.head(10)

        # Create the pie chart using Matplotlib
        fig, ax = plt.subplots(figsize=(8, 8))
        ax.pie(
            top_cities['Number of Skyscrapers'],
            labels=top_cities['City'],
            autopct='%1.1f%%',
            startangle=140,
            colors=plt.cm.Paired.colors
        )
        ax.set_title("Top 10 Cities by Number of Skyscrapers", fontsize=16, color=girly_palette['text_color'])

        # Display the pie chart in Streamlit
        st.pyplot(fig)
    else:
        st.warning("'location.city' column not found in the dataset.")
else:
    st.warning("Data is not defined or empty.")
