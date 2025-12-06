import altair as alt
import pandas as pd
import streamlit as st


@st.cache_data
def load_data():
    """
    Load the dataset. Assumes the dataset is named MHCLD_PUF_2023_clean.csv in the same working directory. 
    Download from Google Drive in links.txt.
    """
    df = pd.read_csv('https://www.dropbox.com/scl/fi/ytd5f8ovcdzjs7yjjvh2o/MHCLD_df_2.csv?rlkey=oe7ldu71x3dp5fv0ctgdsaze9&st=uxuml7uv&dl=1',low_memory=False)
    df['SUB_dia'] = ['NO' if i else 'YES' for i in df['SUB'].isnull()]
    return df

df = load_data()

# create three tabs
tab1, tab2, tab3 = st.tabs(["Diagnosed Mental Disorders", "Substance Use", "Mental Health Service"])

# content for each tab
with tab1:
    st.header("Diagnosed Mental Disorders")
    st.write("!!! Explain what this page is about !!!")

    subset = df.copy()
    


    st.write("### Filters")

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

    # ===== Debug / preview =====
    st.markdown("### Filtered Data Preview for Debug")
    for col in ["AGE", "SEX", "RACE", "EMPLOY", "LIVARAG"]:
        st.write(f"col {col}, unique values are {subset[col].unique()}")
    st.write(subset.head())



    st.subheader("Stacked Bar Charts by Selected Categories")
    
    diagnosis_cols = [col for col in subset.columns if col.endswith("FLG")]
    long_df = subset.melt(
        id_vars=["AGE", "RACE", "SEX", "EMPLOY", "LIVARAG", "STATEFIP"],
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
    
    st.subheader("Stacked Bar Charts by Selected Categories")

    # ----- Sex -----
    agg = (
            long_df.groupby(["Diagnosis", "SEX"])
            .size()
            .reset_index(name="Count")
        )
    agg["Diagnosis"] = agg["Diagnosis"].map(FLAG_TO_NAME)
    st.altair_chart(
        (
            alt.Chart(agg)
            .mark_bar()
            .encode(
                y=alt.Y("Diagnosis:N", title="Disorder Type", axis=alt.Axis(labelLimit=300)),
                x=alt.X("Count:Q", title="Number of Diagnoses"),
                color=alt.Color(f"{"SEX"}:N", title="Sex"),
                tooltip=["Diagnosis:N", f"{"SEX"}:N", "Count:Q"]
            )
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
    st.altair_chart(
        (
            alt.Chart(agg)
            .mark_bar()
            .encode(
                y=alt.Y("Diagnosis:N", title="Disorder Type", axis=alt.Axis(labelLimit=300)),
                x=alt.X("Count:Q", title="Number of Diagnoses"),
                color=alt.Color(f"{"AGE"}:N", title="Age", scale=alt.Scale(scheme="blues")),
                tooltip=["Diagnosis:N", f"{"AGE"}:N", "Count:Q"]
            )
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
    st.altair_chart(
        (
            alt.Chart(agg)
            .mark_bar()
            .encode(
                y=alt.Y("Diagnosis:N", title="Disorder Type", axis=alt.Axis(labelLimit=300)),
                x=alt.X("Count:Q", title="Number of Diagnoses"),
                color=alt.Color(f"{"RACE"}:N", title="Race"),
                tooltip=["Diagnosis:N", f"{"RACE"}:N", "Count:Q"]
            )
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
    st.altair_chart(
        (
            alt.Chart(agg)
            .mark_bar()
            .encode(
                y=alt.Y("Diagnosis:N", title="Disorder Type", axis=alt.Axis(labelLimit=300)),
                x=alt.X("Count:Q", title="Number of Diagnoses"),
                color=alt.Color(f"{"EMPLOY"}:N", title="Social-Economic Status"),
                tooltip=["Diagnosis:N", f"{"EMPLOY"}:N", "Count:Q"]
            )
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
    st.altair_chart(
        (
            alt.Chart(agg)
            .mark_bar()
            .encode(
                y=alt.Y("Diagnosis:N", title="Disorder Type", axis=alt.Axis(labelLimit=300)),
                x=alt.X("Count:Q", title="Number of Diagnoses"),
                color=alt.Color(f"{"LIVARAG"}:N", title="Living Status"),
                tooltip=["Diagnosis:N", f"{"LIVARAG"}:N", "Count:Q"]
            )
            .properties(
                title="Diagnosis Stacked by Living Status (LIVARAG)"
            )
        ),
        use_container_width=True
    )



with tab2:
    st.header("Substance Use")

    st.write("This section provides visualization related to the strength \
             of association between substance use and other mental health disorder\
             diagnoses: which substance abuse conditions are more strongly linked to \
             specific mental disorders.")
    
    st.subheader('Demographics filters')

# ----- Sex -----
    
    sex_options = sorted(df["SEX"].dropna().unique())

    selected_sex = st.radio(
        "Sex (choose one)",
        options=["Both"] + sex_options,
        horizontal=True
    )

    if selected_sex == "Both":
        subset = df[df["SEX"].isin(sex_options)]
    else:
        subset = df[df["SEX"] == selected_sex]

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

# with SUB discorders or not 
    st.subheader('Whether people have a Substance use diagnosis or not')

    dia = st.radio('Substance use related disorders diagonsis', ['NO','YES'])

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
        subset['SAP'] = subset['SAP'].map(SAP_map)

        plot2 = alt.Chart(subset).mark_bar().encode(x = alt.X('SAP:N') , 
                                                    y = alt.Y('mh:Q',
                                                              scale = alt.Scale(type = 'sqrt')).title('count of the mental health disorders'), 
                                                              color = alt.Color("SAP:N"),facet = alt.Column('types_reported:N',columns = 4 ).title('mental health disorders type')).properties( height = 400, 
                                                              width = 100,
                                                              title = 'Distribution of total count of mental health across types and substances use problem(SAP)')
        plot2 = plot2.configure_title(fontSize = 15, anchor = 'middle')

        st.altair_chart(plot2, use_container_width=False)




with tab3:
    st.header("Mental Health Service")
    st.write("This section compares metrics across states.")
    
    # Placeholder for charts
    st.write("Insert charts or maps here.")