import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from turf_analyzer import TURFAnalyzer
from utils import validate_data, create_sample_data
import io

# Page configuration
st.set_page_config(
    page_title="TURF Analysis Tool",
    page_icon="📊",
    layout="wide"
)

# Apply custom CSS
st.markdown("""
    <style>
    .stAlert {border-radius: 5px;}
    .stButton>button {border-radius: 5px;}
    </style>
    """, unsafe_allow_html=True)

def main():
    st.title("📊 TURF Analysis Tool")
    st.markdown("""
    This tool performs TURF (Total Unduplicated Reach and Frequency) analysis to help optimize 
    feature selection and maximize reach across your target audience.
    """)

    # Sidebar for data input and controls
    with st.sidebar:
        st.header("Data Input")
        upload_method = st.radio(
            "Choose input method:",
            ["Upload CSV", "Use Sample Data"]
        )

        if upload_method == "Upload CSV":
            uploaded_file = st.file_uploader(
                "Upload your reach data (CSV)",
                type=['csv'],
                help="CSV should have feature names and reach numbers"
            )
            if uploaded_file:
                try:
                    df = pd.read_csv(uploaded_file)
                    if validate_data(df):
                        st.success("Data loaded successfully!")
                    else:
                        st.error("Invalid data format. Please check the template.")
                        return
                except Exception as e:
                    st.error(f"Error reading file: {str(e)}")
                    return
        else:
            df = create_sample_data()
            st.info("Sample data loaded!")

    # Main content area
    if 'df' in locals():
        # Feature selection
        st.header("Feature Selection")
        col1, col2 = st.columns([2, 1])
        
        with col1:
            selected_features = st.multiselect(
                "Select features to include in analysis:",
                df['Feature'].tolist(),
                default=df['Feature'].tolist()
            )

        with col2:
            max_combinations = st.number_input(
                "Maximum number of features to combine:",
                min_value=1,
                max_value=len(selected_features),
                value=min(3, len(selected_features))
            )

        if st.button("Run TURF Analysis", type="primary"):
            if len(selected_features) < 1:
                st.warning("Please select at least one feature.")
                return

            # Perform TURF analysis
            analyzer = TURFAnalyzer(df[df['Feature'].isin(selected_features)])
            results = analyzer.analyze(max_combinations)

            # Display results
            st.header("Analysis Results")
            
            # Best combination visualization
            best_combo = results['best_combination']
            total_reach = results['max_reach']
            
            st.subheader("Best Feature Combination")
            st.markdown(f"""
            - **Selected Features:** {', '.join(best_combo)}
            - **Total Reach:** {total_reach:,.0f}
            """)

            # Create reach contribution chart
            reach_data = pd.DataFrame({
                'Feature': best_combo,
                'Reach': [df[df['Feature'] == feature]['Reach'].iloc[0] for feature in best_combo]
            })

            fig = px.bar(
                reach_data,
                x='Feature',
                y='Reach',
                title='Individual Feature Reach in Best Combination',
                color='Feature'
            )
            fig.update_layout(showlegend=False)
            st.plotly_chart(fig, use_container_width=True)

            # Display incremental reach
            st.subheader("Incremental Reach Analysis")
            incremental_data = pd.DataFrame({
                'Features': [' + '.join(best_combo[:i+1]) for i in range(len(best_combo))],
                'Cumulative Reach': results['incremental_reach']
            })

            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=incremental_data['Features'],
                y=incremental_data['Cumulative Reach'],
                mode='lines+markers',
                name='Cumulative Reach'
            ))
            fig.update_layout(
                title='Cumulative Reach by Feature Addition',
                xaxis_title='Features Added',
                yaxis_title='Cumulative Reach'
            )
            st.plotly_chart(fig, use_container_width=True)

            # Download results
            results_df = pd.DataFrame({
                'Metric': ['Best Combination', 'Total Reach'],
                'Value': [', '.join(best_combo), total_reach]
            })
            
            csv = results_df.to_csv(index=False)
            st.download_button(
                label="Download Results",
                data=csv,
                file_name="turf_analysis_results.csv",
                mime="text/csv"
            )

if __name__ == "__main__":
    main()
