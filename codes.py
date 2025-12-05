import altair as alt
import pandas as pd
import streamlit as st


@st.cache_data
def load_data():
    """
    Load the dataset. Assumes the dataset is named MHCLD_PUF_2023_clean.csv in the same working directory. 
    Download from Google Drive in links.txt.
    """
    df = pd.read_csv("MHCLD_PUF_2023_clean.csv")
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
    st.write("This section contains deeper analytical visualizations.")
    
    # Placeholder for charts
    st.write("Insert charts or filters here.")

with tab3:
    st.header("Mental Health Service")
    st.write("This section compares metrics across states.")
    
    # Placeholder for charts
    st.write("Insert charts or maps here.")