import altair as alt
import pandas as pd
import streamlit as st
from vega_datasets import data


@st.cache_data
def load_data():
    """
    Load the dataset. Assumes the dataset is named MHCLD_PUF_2023_clean.csv in the same working directory. 
    Download from Google Drive in links.txt.
    """
    df = pd.read_csv('https://www.dropbox.com/scl/fi/lwvmdxby5jx6ns9u2vfgw/MHCLD_sample.csv?rlkey=d49orz62ufwychzdc0olebh1j&st=72zrbbzl&dl=1',low_memory=False)
    df['SUB_dia'] = ['NO' if i else 'YES' for i in df['SUB'].isnull()]
    return df
df = load_data()

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


subset = df.copy()

st.write("### Select Demographic Groups")

# ----- Age -----
AGE_BIN_EDGES = ["under 15", "15", "25", "35", "45", "55", "65", "over 65"]
Age_bin_names = ["Under 15", "15-24", "25-34", "35-44", "45-54", "55-64", "65 and older"]

age_min, age_max = st.select_slider(
    "Age range (non-inclusive on max)",
    options=AGE_BIN_EDGES,
    value=(AGE_BIN_EDGES[0], AGE_BIN_EDGES[-1]),
    help="Each point is a bin edge; select a start and end bin."
)
age_min = AGE_BIN_EDGES.index(age_min)
age_max = AGE_BIN_EDGES.index(age_max)
age_range = Age_bin_names[age_min:age_max]

subset = subset[
    subset["AGE"].isin(age_range)
]

# ----- Sex -----
sex_options = sorted(df["SEX"].dropna().unique())

selected_sex = st.radio(
    "Sex (choose one)",
    options=["Both"] + sex_options,
    horizontal=True
)

if selected_sex == "Both":
    subset = subset[subset["SEX"].isin(sex_options)]
else:
    subset = subset[subset["SEX"] == selected_sex]

# ----- Race -----
race_options = sorted(df["RACE"].dropna().unique())
selected_race = st.multiselect(
    "Race",
    options=race_options,
    default=race_options,
)
subset = subset[subset["RACE"].isin(selected_race)]

# ----- Socio-economic status (EMPLOY) -----
employ_options = sorted(df["EMPLOY"].dropna().unique())
selected_employ = st.multiselect(
    "Employment / Socio-economic status (EMPLOY)",
    options=employ_options,
    default=employ_options,
)
subset = subset[subset["EMPLOY"].isin(selected_employ)]

# ----- Living status (LIVARAG) -----
livarag_options = sorted(df["LIVARAG"].dropna().unique())
selected_livarag = st.multiselect(
    "Living arrangement / status (LIVARAG)",
    options=livarag_options,
    default=livarag_options,
)
subset = subset[subset["LIVARAG"].isin(selected_livarag)]


# ----- Conditional rendering based on view type -----
if view_type == "Diagnosed Mental Disorders":
    # Original Tab 1 content
    diagnosis_cols = [col for col in subset.columns if col.endswith("FLG")]
    long_df = subset.melt(
        id_vars=["AGE", "RACE", "SEX", "EMPLOY", "LIVARAG", "STATEFIP", "STATEFIP_code"],
        value_vars=diagnosis_cols,
        var_name="Diagnosis",
        value_name="HasCondition"
    )
    long_df = long_df[long_df["HasCondition"] == 1]

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
        "OTHERDISFLG": "Other Disorder"
    }
    
    long_df_copy = long_df.copy()
    long_df_copy["Diagnosis"] = long_df_copy["Diagnosis"].map(FLAG_TO_NAME)

    # -----map-----
    st.subheader("Geographical Distribution of Diagnosed Mental Disorders Across US States")
    st.write("Select a mental disorder from the dropdown to visualize its distribution.")
    selected_diagnosis = st.selectbox(
        "Select Diagnosis",
        options=long_df_copy["Diagnosis"].unique()
    )

    # Data aggregation for plotting
    agg_map = long_df_copy[long_df_copy["Diagnosis"] == selected_diagnosis].groupby(["STATEFIP", "STATEFIP_code", "Diagnosis"]).size().reset_index(name="Count")
    agg_map['STATEFIP_code'] = agg_map['STATEFIP_code'].astype(str)
    states = alt.topo_feature(data.us_10m.url, 'states')

    background = alt.Chart(states).mark_geoshape(
        fill='lightgray',
        stroke='white'
    ).project(
        type='albersUsa'
    ).properties(
        height=400
    )   

    map_chart = alt.Chart(states).mark_geoshape(  
        stroke='white',    
    ).encode(
        color=alt.Color('Count:Q', scale=alt.Scale(type='log', scheme='blues'), title='Number of Diagnoses'),
        tooltip=[
            alt.Tooltip('STATEFIP:N', title='State'),
            alt.Tooltip('Count:Q', title='Number of Diagnoses')
        ]
    ).transform_lookup(
        lookup='id',
        from_=alt.LookupData(agg_map, 'STATEFIP_code', ['STATEFIP', 'Count'])
    ).project(
        type='albersUsa'   
    ).properties(
        height=400
    )

    final_chart = (background + map_chart).properties(
        title=f'Geographical Distribution of {selected_diagnosis} Diagnoses Across US States',
        height=400
    )

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
        long_df.groupby(["Diagnosis", "SEX"])
        .size()
        .reset_index(name="Count")
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
                color=alt.Color("SEX:N", title="Sex", legend=alt.Legend(labelLimit=0)),
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
        long_df.groupby(["Diagnosis", "AGE"])
        .size()
        .reset_index(name="Count")
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
                color=alt.Color("AGE:N", title="Age", scale=alt.Scale(scheme="blues"), legend=alt.Legend(labelLimit=0)),
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
        long_df.groupby(["Diagnosis", "RACE"])
        .size()
        .reset_index(name="Count")
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
        long_df.groupby(["Diagnosis", "EMPLOY"])
        .size()
        .reset_index(name="Count")
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
        long_df.groupby(["Diagnosis", "LIVARAG"])
        .size()
        .reset_index(name="Count")
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
    # Original Tab 3 content
    service_cols = ["SPHSERVICE", "CMPSERVICE", "OPISERVICE", "RTCSERVICE", "IJSSERVICE"]
    long_df = subset.melt(
        id_vars=["AGE", "RACE", "SEX", "EMPLOY", "LIVARAG", "STATEFIP", "STATEFIP_code"],
        value_vars=service_cols,
        var_name="Service",
        value_name="HasService"
    )
    
    long_df = long_df[long_df["HasService"] == 1]
    
    SERVICE_TO_NAME = {
        "SPHSERVICE": "State Psychiatric Hospital Services",
        "CMPSERVICE": "SMHA-funded/operated Community-based Program",
        "OPISERVICE": "Other Psychiatric Inpatient",
        "RTCSERVICE": "Residential Treatment Center",
        "IJSSERVICE": "Institutions Under The Justice System"
    }
    
    long_df_copy = long_df.copy()
    long_df_copy["Service"] = long_df_copy["Service"].map(SERVICE_TO_NAME)
    
    # -----map-----
    st.subheader("Geographical Distribution of Mental Health Service Use Across US States")
    st.write("Select a mental health service type from the dropdown to visualize its distribution.")
    selected_service = st.selectbox(
        "Select Service",
        options=long_df_copy["Service"].unique()
    )
    
    # Data aggregation for plotting
    agg_map = long_df_copy[long_df_copy["Service"] == selected_service].groupby(["STATEFIP", "STATEFIP_code", "Service"]).size().reset_index(name="Count")
    agg_map['STATEFIP_code'] = agg_map['STATEFIP_code'].astype(str)
    
    states = alt.topo_feature(data.us_10m.url, 'states')

    background = alt.Chart(states).mark_geoshape(
        fill='lightgray',
        stroke='white'
    ).project(
        type='albersUsa'
    ).properties(
        height=400
    )
    
    map_chart = alt.Chart(states).mark_geoshape(  
        stroke='white'     
    ).encode(
        color=alt.Color('Count:Q', scale=alt.Scale(type='log', scheme='greens'), title='Number of Service Uses'),
        tooltip=[
            alt.Tooltip('STATEFIP:N', title='State'),
            alt.Tooltip('Count:Q', title='Number of Service Uses'),
        ]
    ).transform_lookup(
        lookup='id',
        from_=alt.LookupData(agg_map, 'STATEFIP_code', ['STATEFIP', 'Count'])
    ).project(
        type='albersUsa'   
    ).properties(
        height=400
    )
    
    final_chart = (background + map_chart).properties(
        title=f'Geographical Distribution of {selected_service} Across US States',
        height=400
    )
    
    st.altair_chart(final_chart, use_container_width=True)
    
    # ----- stacked bar charts -----
    st.subheader("Stacked Bar Charts by Selected Categories")

    # ----- Sex -----
    agg = (
        long_df.groupby(["Service", "SEX"])
        .size()
        .reset_index(name="Count")
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
        long_df.groupby(["Service", "AGE"])
        .size()
        .reset_index(name="Count")
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
                    scale=alt.Scale(scheme="blues"),
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
        long_df.groupby(["Service", "RACE"])
        .size()
        .reset_index(name="Count")
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
        long_df.groupby(["Service", "EMPLOY"])
        .size()
        .reset_index(name="Count")
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
        long_df.groupby(["Service", "LIVARAG"])
        .size()
        .reset_index(name="Count")
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
    
    
    st.subheader('Whether people have a Substance use diagnosis or not')
    dia = st.radio('Substance use related disorders diagonsis', ['YES','NO'])
    st.write("If you choose yes, the plots will focus on population with\
            substance-related disorders reported ")
    st.write("If you choose no, the plots will focus on comparing how the mental\
            health disorder distribution differs for the population with a \
            substance-related problem, but no diagnosis, and the population with no \
            substance-related problem ")
    subset = subset[subset["SUB_dia"] == dia]
    if dia == 'YES':
        subset = subset[["TRAUSTREFLG", "ANXIETYFLG", "ADHDFLG", "CONDUCTFLG",
                        "DELIRDEMFLG", "BIPOLARFLG", "DEPRESSFLG", "ODDFLG",
                        "PDDFLG", "PERSONFLG", "SCHIZOFLG", "OTHERDISFLG","SUB"]].groupby('SUB').sum()
        subset.columns = ['mh_' + i for i in subset.columns]
        subset = subset.reset_index()
        subset = pd.wide_to_long(subset, stubnames='mh', i='SUB', j='types_reported',sep='_', suffix=r'\w+').reset_index()
        brush = alt.selection_interval( encodings=['x'])
        
        chart = alt.Chart(subset).mark_rect().encode(
            x=alt.X("types_reported:N"),
            y=alt.Y("SUB:N", title="substance-related disorders"),
            color=alt.Color("mh:Q",scale = alt.Scale(type = 'log',domain=(0.01, 1000), clamp=True),legend = alt.Legend(title = 'log(count)')),
            tooltip=[
                alt.Tooltip("mh:Q", title="count"),
                alt.Tooltip("SUB", title="Asubstnce disorders"),
                alt.Tooltip("types_reported", title="mental health disorders")
                ],).properties(width = 600).add_params(brush)
        t = subset.groupby(["SUB"])['mh'].sum()
        map_pop = dict(zip(t.index.values, t.values))
        subset['pop'] = subset['SUB'].map(map_pop)
        subset['percentage'] = subset['mh']/subset['pop']
        chart_bar = alt.Chart(subset
                            ).mark_bar().encode(x=alt.X("sum(percentage):Q",title = 'Sum of percentage'),
                                                y=alt.Y("SUB:N", title="substance-related disorders"),tooltip = [
                                                    alt.Tooltip("sum(percentage):Q", title="Sum of Percentage"),
                                                    alt.Tooltip("SUB:N", title="substance-related disorders")]).transform_filter(brush)
        combine_c = alt.vconcat(chart, chart_bar)
        st.altair_chart(combine_c, use_container_width=True)
    if dia == 'NO':
        subset = subset[["TRAUSTREFLG", "ANXIETYFLG", "ADHDFLG", "CONDUCTFLG",
                        "DELIRDEMFLG", "BIPOLARFLG", "DEPRESSFLG", "ODDFLG",
                        "PDDFLG", "PERSONFLG", "SCHIZOFLG", "OTHERDISFLG",'SAP']].set_index('SAP')
        subset.columns = ['mh_' + i for i in subset.columns]
        subset = subset.reset_index().dropna()
        subset['id'] = subset.index
        subset = pd.wide_to_long(subset, stubnames='mh', i='id', j='types_reported',sep='_', suffix=r'\w+')
        subset = subset.groupby(['types_reported','SAP']).sum()['mh'].reset_index()
        subset['SAP'] = subset['SAP'].astype(str)
        
        SAP_map = {'1.0':'problem','0.0':'no problen'}
        type_map = {
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
        "OTHERDISFLG": "Other Disorder"}
        subset['SAP'] = subset['SAP'].map(SAP_map)
        subset['types_reported'] = subset['types_reported'].map(type_map)
        plot2 = alt.Chart(subset).mark_bar().encode(x = alt.X('SAP:N') , 
                                                y = alt.Y('mh:Q',
                                                            scale = alt.Scale(type = 'sqrt')).title('count of the mental health disorders'), 
                                                            color = alt.Color("SAP:N"),facet = alt.Column('types_reported:N',columns = 4 ).title('mental health disorders type')).properties( height = 400, 
                                                            width = 100,
                                                            title = 'Distribution of total count of mental health across types and substances use problem(SAP)')
        plot2 = plot2.configure_title(fontSize = 15, anchor = 'middle')
        st.altair_chart(plot2, use_container_width=False)


