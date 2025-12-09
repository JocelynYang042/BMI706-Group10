import altair as alt
import pandas as pd
import streamlit as st
from pathlib import Path
from vega_datasets import data

BASE_PATH = Path(__file__).resolve().parent
AGE_BIN_LABELS = ["Under 15", "15-24", "25-34", "35-44", "45-54", "55-64", "65 and older"]
DIAGNOSIS_COLS = [
    "TRAUSTREFLG",
    "ANXIETYFLG",
    "ADHDFLG",
    "CONDUCTFLG",
    "DELIRDEMFLG",
    "BIPOLARFLG",
    "DEPRESSFLG",
    "ODDFLG",
    "PDDFLG",
    "PERSONFLG",
    "SCHIZOFLG",
    "ALCSUBFLG",
    "OTHERDISFLG",
]
SERVICE_COLS = ["SPHSERVICE", "CMPSERVICE", "OPISERVICE", "RTCSERVICE", "IJSSERVICE"]
FLAG_TO_NAME = {
    "TRAUSTREFLG": "Trauma & Stressor Disorder",
    "ANXIETYFLG": "Anxiety Disorder",
    "ADHDFLG": "ADHD",
    "CONDUCTFLG": "Conduct Disorder",
    "DELIRDEMFLG": "Delirium / Dementia",
    "BIPOLARFLG": "Bipolar Disorder",
    "DEPRESSFLG": "Depression",
    "ODDFLG": "Oppositional Defiant Disorder",
    "PDDFLG": "Pervasive Developmental Disorder",
    "PERSONFLG": "Personality Disorder",
    "SCHIZOFLG": "Schizophrenia",
    "ALCSUBFLG": "Alcohol Use Disorder",
    "OTHERDISFLG": "Other Disorder",
}
SERVICE_TO_NAME = {
    "SPHSERVICE": "State Psychiatric Hospital Services",
    "CMPSERVICE": "SMHA-funded/operated Community-based Program",
    "OPISERVICE": "Other Psychiatric Inpatient",
    "RTCSERVICE": "Residential Treatment Center",
    "IJSSERVICE": "Institutions Under The Justice System",
}
TYPE_MAP = FLAG_TO_NAME


FILTER_COLUMNS = ["RACE", "SEX", "EMPLOY", "LIVARAG"]


@st.cache_data
def load_aggregated_data():
    """
    Load pre-aggregated datasets produced by precompute_stats.py.
    Missing demographic values are filled with 'Missing' so the UI can include them.
    """
    demo_path = BASE_PATH / "data" / "demographic_service_stats.csv"
    substance_path = BASE_PATH / "data" / "substance_stats.csv"
    demographic = pd.read_csv(demo_path, dtype={"STATEFIP_code": str})
    substance = pd.read_csv(substance_path, dtype={"SAP": str})

    for col in FILTER_COLUMNS:
        demographic[col] = demographic[col].fillna("Missing")
        substance[col] = substance[col].fillna("Missing")

    if "SUB_dia" not in substance.columns:
        substance["SUB_dia"] = substance["SUB"].notna().map({True: "YES", False: "NO"})
    return demographic, substance


demographic_df, substance_df = load_aggregated_data()
filter_reference = pd.concat(
    [
        demographic_df[["AGE", "RACE", "SEX", "EMPLOY", "LIVARAG"]],
        substance_df[["AGE", "RACE", "SEX", "EMPLOY", "LIVARAG"]],
    ],
    ignore_index=True,
)


def apply_demographic_filters(
    df: pd.DataFrame,
    age_range: list[str],
    sex_values: list[str],
    races: list[str],
    employ_status: list[str],
    living_status: list[str],
) -> pd.DataFrame:
    subset = df[df["AGE"].isin(age_range)]
    subset = subset[subset["SEX"].isin(sex_values)]
    subset = subset[subset["RACE"].isin(races)]
    subset = subset[subset["EMPLOY"].isin(employ_status)]
    subset = subset[subset["LIVARAG"].isin(living_status)]
    return subset

# create two tabs (merged tab 1 and 3)
#tab1, tab2 = st.tabs(["Diagnosed Mental Disorders & Mental Health Service", "Substance Use"])

# content for merged tab1
#with tab1:
st.header(" Mental Health Client-Level Data (MH-CLD) Visualizer ")

# Add radio button to choose between diagnosis and service statistics
view_type = st.radio(
    "Select Statistics Type",
    options=["Diagnosed Mental Disorders", "Mental Health Service Use","Substance Use"],
    horizontal=True
)

if view_type == "Diagnosed Mental Disorders":
    st.write("This section provides visualization related to the distribution of various diagnosed mental disorders across different demographic groups in the US population.")
elif view_type == "Mental Health Service Use":
    st.write("This section compares the number of mental health services received across the states.")
else:
    st.write("This section provides visualization related to the strength \
            of association between substance use and other mental health disorder\
            diagnoses: which substance abuse conditions are more strongly linked to \
            specific mental disorders.")


filter_box = st.sidebar.container()
filter_box.header("Select Demographic Groups")

# ----- Age -----
AGE_BIN_EDGES = ["under 15", "15", "25", "35", "45", "55", "65", "over 65"]

age_min, age_max = filter_box.select_slider(
    "Age range (non-inclusive on max)",
    options=AGE_BIN_EDGES,
    value=(AGE_BIN_EDGES[0], AGE_BIN_EDGES[-1]),
    help="Each point is a bin edge; select a start and end bin."
)
age_min = AGE_BIN_EDGES.index(age_min)
age_max = AGE_BIN_EDGES.index(age_max)
age_range = AGE_BIN_LABELS[age_min:age_max]

# ----- Sex -----
sex_options = sorted(filter_reference["SEX"].dropna().unique())

selected_sex = filter_box.radio(
    "Sex (choose one)",
    options=["Both"] + sex_options,
    horizontal=True
)

sex_filter = sex_options if selected_sex == "Both" else [selected_sex]

# ----- Race -----
race_options = sorted(filter_reference["RACE"].dropna().unique())
selected_race = filter_box.multiselect(
    "Race",
    options=race_options,
    default=race_options,
)

# ----- Socio-economic status (EMPLOY) -----
employ_options = sorted(filter_reference["EMPLOY"].dropna().unique())
selected_employ = filter_box.multiselect(
    "Employment / Socio-economic status (EMPLOY)",
    options=employ_options,
    default=employ_options,
)

# ----- Living status (LIVARAG) -----
livarag_options = sorted(filter_reference["LIVARAG"].dropna().unique())
selected_livarag = filter_box.multiselect(
    "Living arrangement / status (LIVARAG)",
    options=livarag_options,
    default=livarag_options,
)
demographic_subset = apply_demographic_filters(
    demographic_df,
    age_range,
    sex_filter,
    selected_race,
    selected_employ,
    selected_livarag,
)
substance_subset = apply_demographic_filters(
    substance_df,
    age_range,
    sex_filter,
    selected_race,
    selected_employ,
    selected_livarag,
)


# ----- Conditional rendering based on view type -----
if view_type == "Diagnosed Mental Disorders":
    if demographic_subset.empty:
        st.warning("No diagnosed disorders found for the selected demographic filters.")
        st.stop()

    state_totals = (
        demographic_subset.groupby(["STATEFIP", "STATEFIP_code"], as_index=False)["CLIENT_COUNT"]
        .sum()
        .rename(columns={"CLIENT_COUNT": "TotalClients"})
    )

    long_df = demographic_subset.melt(
        id_vars=["AGE", "RACE", "SEX", "EMPLOY", "LIVARAG", "STATEFIP", "STATEFIP_code"],
        value_vars=DIAGNOSIS_COLS,
        var_name="Diagnosis",
        value_name="Count"
    )
    long_df = long_df[long_df["Count"] > 0]
    long_df_copy = long_df.copy()
    long_df_copy["Diagnosis"] = long_df_copy["Diagnosis"].map(FLAG_TO_NAME)

    # -----map-----
    st.subheader("Geographical Distribution of Diagnosed Mental Disorders Across US States")
    st.write("Select a mental disorder from the dropdown to visualize its distribution.")
    diagnosis_options = long_df_copy["Diagnosis"].dropna().unique()
    if len(diagnosis_options) == 0:
        st.warning("No diagnoses available after filtering.")
        st.stop()

    selected_diagnosis = st.selectbox(
        "Select Diagnosis",
        options=sorted(diagnosis_options)
    )

    # Data aggregation for plotting
    agg_map = (
        long_df_copy[long_df_copy["Diagnosis"] == selected_diagnosis]
        .groupby(["STATEFIP", "STATEFIP_code", "Diagnosis"], as_index=False)["Count"]
        .sum()
    )
    agg_map['STATEFIP_code'] = agg_map['STATEFIP_code'].astype(str)
    map_data = agg_map.merge(state_totals, on=["STATEFIP", "STATEFIP_code"], how="left")
    map_data["RatePercent"] = (
        map_data["Count"] / map_data["TotalClients"].replace({0: pd.NA})
    ).fillna(0) * 100
    states = alt.topo_feature(data.us_10m.url, 'states')

    background = alt.Chart(states).mark_geoshape(
        fill='lightgray',
        stroke='white'
    ).project(
        type='albersUsa'
    ).properties(
        width=320,
        height=400
    )   

    map_chart = alt.Chart(states).mark_geoshape(  
        stroke='white',    
    ).encode(
        color=alt.Color('Count:Q', scale=alt.Scale(type='log', scheme='blues'), title='Number of Diagnoses'),
        tooltip=[
            alt.Tooltip('STATEFIP:N', title='State'),
            alt.Tooltip('Count:Q', title='Number of Diagnoses'),
            alt.Tooltip('RatePercent:Q', title='Percent Diagnosed', format='.2f')
        ]
    ).transform_lookup(
        lookup='id',
        from_=alt.LookupData(map_data, 'STATEFIP_code', ['STATEFIP', 'Count', 'RatePercent'])
    ).project(
        type='albersUsa'   
    )

    diagnosis_rate_max = float(map_data["RatePercent"].max() or 1)
    rate_chart = alt.Chart(states).mark_geoshape(
        stroke='white',
    ).encode(
        color=alt.Color(
            'RatePercent:Q',
            scale=alt.Scale(scheme='tealblues', domain=[0, diagnosis_rate_max]),
            title='Diagnosed (%)'
        ),
        tooltip=[
            alt.Tooltip('STATEFIP:N', title='State'),
            alt.Tooltip('RatePercent:Q', title='Percent Diagnosed', format='.2f'),
            alt.Tooltip('Count:Q', title='Number of Diagnoses')
        ]
    ).transform_lookup(
        lookup='id',
        from_=alt.LookupData(map_data, 'STATEFIP_code', ['STATEFIP', 'RatePercent', 'Count'])
    ).project(
        type='albersUsa'
    )

    count_plot = (background + map_chart).properties(
        title=f'Number of {selected_diagnosis} Diagnoses',
    )
    rate_plot = (background + rate_chart).properties(
        title=f'Share of {selected_diagnosis} Diagnoses out of All Clients (%) in Each State',
    )

    final_chart = alt.vconcat(count_plot, rate_plot).resolve_scale(color="independent")

    st.markdown("""
    <style>
        iframe[title="streamlit_extras.chart"] {
            display: block;
            margin-left: auto;
            margin-right: auto;
        }
    </style>
    """, unsafe_allow_html=True)

    st.altair_chart(final_chart, use_container_width=True)

    # ----- stacked bar charts -----
    st.subheader("Stacked Bar Charts by Selected Categories")

    # ----- Sex -----
    agg = (
        long_df.groupby(["Diagnosis", "SEX"], as_index=False)["Count"]
        .sum()
    )
    agg["Diagnosis"] = agg["Diagnosis"].map(FLAG_TO_NAME)
    sex_selection = alt.selection_point(fields=["SEX"], bind="legend")
    st.altair_chart(
        (
            alt.Chart(agg)
            .mark_bar()
            .encode(
                y=alt.Y("Diagnosis:N", title="Disorder Type", axis=alt.Axis(labelLimit=300)),
                x=alt.X("Count:Q", title="Number of Diagnoses"),
                color=alt.Color("SEX:N", title="Sex", legend=alt.Legend(labelLimit=0), domain=["Female", "Male", "Missing"], range=["#e78ac3", "#8da0cb", "red"]),
                tooltip=["Diagnosis:N", "SEX:N", "Count:Q"],
                opacity=alt.condition(sex_selection, alt.value(1), alt.value(0.2))
            )
            .add_params(sex_selection)
            .properties(
                title="Diagnosis Stacked by Sex"
            )
        ),
        use_container_width=True
    )

    # ----- Age -----
    agg = (
        long_df.groupby(["Diagnosis", "AGE"], as_index=False)["Count"]
        .sum()
    )
    agg["Diagnosis"] = agg["Diagnosis"].map(FLAG_TO_NAME)
    age_selection = alt.selection_point(fields=["AGE"], bind="legend")
    st.altair_chart(
        (
            alt.Chart(agg)
            .mark_bar()
            .encode(
                y=alt.Y("Diagnosis:N", title="Disorder Type", axis=alt.Axis(labelLimit=300)),
                x=alt.X("Count:Q", title="Number of Diagnoses"),
                color=alt.Color(
                    "AGE:N",
                    title="Age",
                    scale=alt.Scale(scheme="blues", domain=AGE_BIN_LABELS),
                    legend=alt.Legend(labelLimit=0)
                ),
                tooltip=["Diagnosis:N", "AGE:N", "Count:Q"],
                opacity=alt.condition(age_selection, alt.value(1), alt.value(0.2))
            )
            .add_params(age_selection)
            .properties(
                title="Diagnosis Stacked by Age"
            )
        ),
        use_container_width=True
    )

    # ----- Race -----
    agg = (
        long_df.groupby(["Diagnosis", "RACE"], as_index=False)["Count"]
        .sum()
    )
    agg["Diagnosis"] = agg["Diagnosis"].map(FLAG_TO_NAME)
    race_selection = alt.selection_point(fields=["RACE"], bind="legend")
    st.altair_chart(
        (
            alt.Chart(agg)
            .mark_bar()
            .encode(
                y=alt.Y("Diagnosis:N", title="Disorder Type", axis=alt.Axis(labelLimit=300)),
                x=alt.X("Count:Q", title="Number of Diagnoses"),
                color=alt.Color("RACE:N", title="Race", legend=alt.Legend(labelLimit=0)),
                tooltip=["Diagnosis:N", "RACE:N", "Count:Q"],
                opacity=alt.condition(race_selection, alt.value(1), alt.value(0.2))
            )
            .add_params(race_selection)
            .properties(
                title="Diagnosis Stacked by Race"
            )
        ),
        use_container_width=True
    )

    # ----- Social-econ status -----
    agg = (
        long_df.groupby(["Diagnosis", "EMPLOY"], as_index=False)["Count"]
        .sum()
    )
    agg["Diagnosis"] = agg["Diagnosis"].map(FLAG_TO_NAME)
    employ_selection = alt.selection_point(fields=["EMPLOY"], bind="legend")
    st.altair_chart(
        (
            alt.Chart(agg)
            .mark_bar()
            .encode(
                y=alt.Y("Diagnosis:N", title="Disorder Type", axis=alt.Axis(labelLimit=300)),
                x=alt.X("Count:Q", title="Number of Diagnoses"),
                color=alt.Color("EMPLOY:N", title="Social-Economic Status", legend=alt.Legend(labelLimit=0)),
                tooltip=["Diagnosis:N", "EMPLOY:N", "Count:Q"],
                opacity=alt.condition(employ_selection, alt.value(1), alt.value(0.2))
            )
            .add_params(employ_selection)
            .properties(
                title="Diagnosis Stacked by Social-Economic Status (EMPLOY)"
            )
        ),
        use_container_width=True
    )

    # ----- Living status -----
    agg = (
        long_df.groupby(["Diagnosis", "LIVARAG"], as_index=False)["Count"]
        .sum()
    )
    agg["Diagnosis"] = agg["Diagnosis"].map(FLAG_TO_NAME)
    livarag_selection = alt.selection_point(fields=["LIVARAG"], bind="legend")
    st.altair_chart(
        (
            alt.Chart(agg)
            .mark_bar()
            .encode(
                y=alt.Y("Diagnosis:N", title="Disorder Type", axis=alt.Axis(labelLimit=300)),
                x=alt.X("Count:Q", title="Number of Diagnoses"),
                color=alt.Color("LIVARAG:N", title="Living Status", legend=alt.Legend(labelLimit=0)),
                tooltip=["Diagnosis:N", "LIVARAG:N", "Count:Q"],
                opacity=alt.condition(livarag_selection, alt.value(1), alt.value(0.2))
            )
            .add_params(livarag_selection)
            .properties(
                title="Diagnosis Stacked by Living Status (LIVARAG)"
            )
        ),
        use_container_width=True
    )

elif view_type == "Mental Health Service Use": # Mental Health Service Use
    if demographic_subset.empty:
        st.warning("No service utilization data matched the selected demographic filters.")
        st.stop()

    state_totals = (
        demographic_subset.groupby(["STATEFIP", "STATEFIP_code"], as_index=False)["CLIENT_COUNT"]
        .sum()
        .rename(columns={"CLIENT_COUNT": "TotalClients"})
    )

    long_df = demographic_subset.melt(
        id_vars=["AGE", "RACE", "SEX", "EMPLOY", "LIVARAG", "STATEFIP", "STATEFIP_code"],
        value_vars=SERVICE_COLS,
        var_name="Service",
        value_name="Count"
    )
    
    long_df = long_df[long_df["Count"] > 0]
    long_df_copy = long_df.copy()
    long_df_copy["Service"] = long_df_copy["Service"].map(SERVICE_TO_NAME)
    
    # -----map-----
    st.subheader("Geographical Distribution of Mental Health Service Use Across US States")
    st.write("Select a mental health service type from the dropdown to visualize its distribution.")
    service_options = long_df_copy["Service"].dropna().unique()
    if len(service_options) == 0:
        st.warning("No services available after filtering.")
        st.stop()

    selected_service = st.selectbox(
        "Select Service",
        options=sorted(service_options)
    )
    
    # Data aggregation for plotting
    agg_map = (
        long_df_copy[long_df_copy["Service"] == selected_service]
        .groupby(["STATEFIP", "STATEFIP_code", "Service"], as_index=False)["Count"]
        .sum()
    )
    agg_map['STATEFIP_code'] = agg_map['STATEFIP_code'].astype(str)
    map_data = agg_map.merge(state_totals, on=["STATEFIP", "STATEFIP_code"], how="left")
    map_data["RatePercent"] = (
        map_data["Count"] / map_data["TotalClients"].replace({0: pd.NA})
    ).fillna(0) * 100
    
    states = alt.topo_feature(data.us_10m.url, 'states')

    background = alt.Chart(states).mark_geoshape(
        fill='lightgray',
        stroke='white'
    ).project(
        type='albersUsa'
    ).properties(
        width=320,
        height=400
    )
    
    map_chart = alt.Chart(states).mark_geoshape(  
        stroke='white'     
    ).encode(
        color=alt.Color('Count:Q', scale=alt.Scale(type='log', scheme='greens'), title='Number of Service Uses'),
        tooltip=[
            alt.Tooltip('STATEFIP:N', title='State'),
            alt.Tooltip('Count:Q', title='Number of Service Uses'),
            alt.Tooltip('RatePercent:Q', title='Percent Receiving Service', format='.2f'),
        ]
    ).transform_lookup(
        lookup='id',
        from_=alt.LookupData(map_data, 'STATEFIP_code', ['STATEFIP', 'Count', 'RatePercent'])
    ).project(
        type='albersUsa'   
    )
    
    service_rate_max = float(map_data["RatePercent"].max() or 1)
    rate_chart = alt.Chart(states).mark_geoshape(
        stroke='white'
    ).encode(
        color=alt.Color(
            'RatePercent:Q',
            scale=alt.Scale(scheme='yellowgreen', domain=[0, service_rate_max]),
            title='Service Use (%)'
        ),
        tooltip=[
            alt.Tooltip('STATEFIP:N', title='State'),
            alt.Tooltip('RatePercent:Q', title='Percent Receiving Service', format='.2f'),
            alt.Tooltip('Count:Q', title='Number of Service Uses'),
        ]
    ).transform_lookup(
        lookup='id',
        from_=alt.LookupData(map_data, 'STATEFIP_code', ['STATEFIP', 'RatePercent', 'Count'])
    ).project(
        type='albersUsa'
    )

    count_plot = (background + map_chart).properties(
        title=f'Number of {selected_service} Uses',
    )
    rate_plot = (background + rate_chart).properties(
        title=f'Share of {selected_service} Uses out of All Clients (%) in Each State',
    )

    final_chart = alt.vconcat(count_plot, rate_plot).resolve_scale(color="independent")
    
    st.altair_chart(final_chart, use_container_width=True)
    
    # ----- stacked bar charts -----
    st.subheader("Stacked Bar Charts by Selected Categories")

    # ----- Sex -----
    agg = (
        long_df.groupby(["Service", "SEX"], as_index=False)["Count"]
        .sum()
    )
    agg["Service"] = agg["Service"].map(SERVICE_TO_NAME)
    service_sex_selection = alt.selection_point(fields=["SEX"], bind="legend")
    st.altair_chart(
        (
            alt.Chart(agg)
            .mark_bar()
            .encode(
                y=alt.Y(
                    "Service:N",
                    title="Service Type",
                    axis=alt.Axis(labelLimit=300, labelPadding=10, titlePadding=80)
                ),
                x=alt.X("Count:Q", title="Number of Service Uses"),
                color=alt.Color("SEX:N", title="Sex", legend=alt.Legend(labelLimit=0)),
                tooltip=["Service:N", "SEX:N", "Count:Q"],
                opacity=alt.condition(service_sex_selection, alt.value(1), alt.value(0.2))
            )
            .add_params(service_sex_selection)
            .properties(
                title="Service Use Stacked by Sex",
                width=800
            )
        ),
        use_container_width=False
    )

    # ----- Age -----
    agg = (
        long_df.groupby(["Service", "AGE"], as_index=False)["Count"]
        .sum()
    )
    agg["Service"] = agg["Service"].map(SERVICE_TO_NAME)
    service_age_selection = alt.selection_point(fields=["AGE"], bind="legend")
    st.altair_chart(
        (
            alt.Chart(agg)
            .mark_bar()
            .encode(
                y=alt.Y(
                    "Service:N",
                    title="Service Type",
                    axis=alt.Axis(labelLimit=300, labelPadding=10, titlePadding=80)
                ),
                x=alt.X("Count:Q", title="Number of Service Uses"),
                color=alt.Color(
                    "AGE:N",
                    title="Age",
                    scale=alt.Scale(scheme="blues", domain=AGE_BIN_LABELS),
                    legend=alt.Legend(labelLimit=0)
                ),
                tooltip=["Service:N", "AGE:N", "Count:Q"],
                opacity=alt.condition(service_age_selection, alt.value(1), alt.value(0.2))
            )
            .add_params(service_age_selection)
            .properties(
                title="Service Use Stacked by Age",
                width=800
            )
        ),
        use_container_width=False
    )

    # ----- Race -----
    agg = (
        long_df.groupby(["Service", "RACE"], as_index=False)["Count"]
        .sum()
    )
    agg["Service"] = agg["Service"].map(SERVICE_TO_NAME)
    service_race_selection = alt.selection_point(fields=["RACE"], bind="legend")
    st.altair_chart(
        (
            alt.Chart(agg)
            .mark_bar()
            .encode(
                y=alt.Y(
                    "Service:N",
                    title="Service Type",
                    axis=alt.Axis(labelLimit=300, labelPadding=10, titlePadding=80)
                ),
                x=alt.X("Count:Q", title="Number of Service Uses"),
                color=alt.Color("RACE:N", title="Race", legend=alt.Legend(labelLimit=0)),
                tooltip=["Service:N", "RACE:N", "Count:Q"],
                opacity=alt.condition(service_race_selection, alt.value(1), alt.value(0.2))
            )
            .add_params(service_race_selection)
            .properties(
                title="Service Use Stacked by Race",
                width=800
            )
        ),
        use_container_width=False
    )

    # ----- Social-econ status -----
    agg = (
        long_df.groupby(["Service", "EMPLOY"], as_index=False)["Count"]
        .sum()
    )
    agg["Service"] = agg["Service"].map(SERVICE_TO_NAME)
    service_employ_selection = alt.selection_point(fields=["EMPLOY"], bind="legend")
    st.altair_chart(
        (
            alt.Chart(agg)
            .mark_bar()
            .encode(
                y=alt.Y(
                    "Service:N",
                    title="Service Type",
                    axis=alt.Axis(labelLimit=300, labelPadding=10, titlePadding=80)
                ),
                x=alt.X("Count:Q", title="Number of Service Uses"),
                color=alt.Color(
                    "EMPLOY:N",
                    title="Social-Economic Status",
                    legend=alt.Legend(labelLimit=0)
                ),
                tooltip=["Service:N", "EMPLOY:N", "Count:Q"],
                opacity=alt.condition(service_employ_selection, alt.value(1), alt.value(0.2))
            )
            .add_params(service_employ_selection)
            .properties(
                title="Service Use Stacked by Social-Economic Status (EMPLOY)",
                width=800
            )
        ),
        use_container_width=False
    )

    # ----- Living status -----
    agg = (
        long_df.groupby(["Service", "LIVARAG"], as_index=False)["Count"]
        .sum()
    )
    agg["Service"] = agg["Service"].map(SERVICE_TO_NAME)
    service_livarag_selection = alt.selection_point(fields=["LIVARAG"], bind="legend")
    st.altair_chart(
        (
            alt.Chart(agg)
            .mark_bar()
            .encode(
                y=alt.Y(
                    "Service:N",
                    title="Service Type",
                    axis=alt.Axis(labelLimit=300, labelPadding=10, titlePadding=80)
                ),
                x=alt.X("Count:Q", title="Number of Service Uses"),
                color=alt.Color("LIVARAG:N", title="Living Status", legend=alt.Legend(labelLimit=0)),
                tooltip=["Service:N", "LIVARAG:N", "Count:Q"],
                opacity=alt.condition(service_livarag_selection, alt.value(1), alt.value(0.2))
            )
            .add_params(service_livarag_selection)
            .properties(
                title="Service Use Stacked by Living Status (LIVARAG)",
                width=800
            )
        ),
        use_container_width=False
    )
else:
    
    
    st.subheader('Whether People Have a Substance Use Diagnosis or Not')
    dia = st.radio('Filter to only people WITH a substance use diagnosis?', ['YES','NO'])
    st.write("If you choose yes, the plots will focus on population with\
            substance-related disorders reported ")
    st.write("If you choose no, the plots will focus on comparing how the mental\
            health disorder distribution differs for the population with a \
            substance-related problem, but no diagnosis, and the population with no \
            substance-related problem ")
    subset = substance_subset[substance_subset["SUB_dia"] == dia]
    if subset.empty:
        st.warning("No records matched the selected demographic filters for this substance-use view.")
        st.stop()

    if dia == 'YES':
        subset = subset.dropna(subset=["SUB"])
        if subset.empty:
            st.warning("No substance-use diagnoses available for the selected filters.")
            st.stop()

        subset = subset.melt(
            id_vars=["SUB"],
            value_vars=DIAGNOSIS_COLS,
            var_name="types_reported",
            value_name="mh"
        )
        subset = (
            subset.groupby(["SUB", "types_reported"], as_index=False)["mh"]
            .sum()
        )
        subset = subset[subset["mh"] > 0]
        if subset.empty:
            st.warning("No diagnosis counts available for the selected substance-use category.")
            st.stop()
        subset["types_reported"] = subset["types_reported"].map(TYPE_MAP).fillna(subset["types_reported"])
        brush = alt.selection_interval(encodings=['x'], name="diag_brush")
        
        chart = alt.Chart(subset).mark_rect().encode(
            x=alt.X("types_reported:N", title="Mental health disorders"),
            y=alt.Y("SUB:N", title="Substance-related disorders"),
            color=alt.Color("mh:Q", scale=alt.Scale(type='log', clamp=True), legend=alt.Legend(title='log(count)')),
            tooltip=[
                alt.Tooltip("mh:Q", title="count"),
                alt.Tooltip("SUB", title="Substance disorders"),
                alt.Tooltip("types_reported", title="Mental health disorders")
                ],).properties(width=600).add_params(brush)
        t = subset.groupby(["SUB"])['mh'].sum()
        map_pop = dict(zip(t.index.values, t.values))
        subset['pop'] = subset['SUB'].map(map_pop)
        subset['percentage'] = subset['mh']/subset['pop']
        chart_bar = alt.Chart(subset
                            ).mark_bar().encode(x=alt.X("sum(percentage):Q",title = 'Sum of percentage',
                                                        scale=alt.Scale(
                                                            domainMin=0,
                                                            domainMax=alt.ExprRef("length(data('diag_brush_store')) ? null : 1"),
                                                            clamp=True
                                                        )),
                                                y=alt.Y("SUB:N", title="substance-related disorders"),tooltip = [
                                                    alt.Tooltip("sum(percentage):Q", title="Sum of Percentage"),
                                                    alt.Tooltip("SUB:N", title="substance-related disorders")]).transform_filter(brush)
        combine_c = alt.vconcat(chart, chart_bar)
        st.altair_chart(combine_c, use_container_width=True)
    if dia == 'NO':
        subset = subset.melt(
            id_vars=["SAP"],
            value_vars=DIAGNOSIS_COLS,
            var_name="types_reported",
            value_name="mh"
        )
        subset = (
            subset.groupby(['types_reported','SAP'], as_index=False)["mh"]
            .sum()
        )
        subset = subset[subset["mh"] > 0]
        if subset.empty:
            st.warning("No counts available for the selected filters and SAP grouping.")
            st.stop()
        subset['SAP'] = subset['SAP'].fillna('missing').astype(str)
        
        SAP_map = {'1.0':'problem','0.0':'no problem','missing': 'missing'}
        subset['SAP'] = subset['SAP'].map(SAP_map).fillna(subset['SAP'])
        subset['types_reported'] = subset['types_reported'].map(TYPE_MAP).fillna(subset['types_reported'])
        plot2 = alt.Chart(subset).mark_bar().encode(x = alt.X('SAP:N') , 
                                                y = alt.Y('mh:Q',
                                                            scale = alt.Scale(type = 'sqrt')).title('count of the mental health disorders'), 
                                                            color = alt.Color("SAP:N"),facet = alt.Column('types_reported:N',columns = 4 ).title('mental health disorders type')).properties( height = 400, 
                                                            width = 100,
                                                            title = 'Distribution of total count of mental health across types and substances use problem(SAP)')
        plot2 = plot2.configure_title(fontSize = 15, anchor = 'middle')
        st.altair_chart(plot2, use_container_width=False)
