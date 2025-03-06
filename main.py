import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from turf_analyzer import TURFAnalyzer
from utils import validate_data, create_sample_data
import io
import xlsxwriter
from datetime import datetime

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

def get_top_features(df, n=5):
    """Get the top n features by total reach"""
    feature_reach = df.sum().sort_values(ascending=False)
    return feature_reach.index.tolist()[:n]

def create_excel_report(results, df, best_combo, reach_metrics_df, viz_data):
    """Create a detailed Excel report with charts and tables"""
    output = io.BytesIO()

    # Create Excel writer object
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        workbook = writer.book

        # Add summary sheet
        summary_df = pd.DataFrame({
            'Metric': ['Best Combination', 'Total Reach', 'Reach Percentage', 'Total Respondents'],
            'Value': [
                ', '.join(best_combo),
                f"{results['max_reach']:,.0f}",
                f"{(results['max_reach'] / results['total_respondents'] * 100):.1f}%",
                f"{results['total_respondents']:,.0f}"
            ]
        })
        summary_df.to_excel(writer, sheet_name='Summary', index=False)

        # Add detailed metrics sheet
        reach_metrics_df.to_excel(writer, sheet_name='Detailed Metrics', index=False)

        # Create charts sheet
        chart_sheet = workbook.add_worksheet('Charts')

        # Add reach comparison chart
        chart1 = workbook.add_chart({'type': 'column'})

        # Write data for the chart
        chart_data = pd.DataFrame({
            'Feature': viz_data['Feature'],
            'Marginal Reach (%)': viz_data['Marginal Pct'],
            'Incremental Reach (%)': viz_data['Incremental Pct'],
            'Cumulative Reach (%)': viz_data['Cumulative Pct']
        })
        chart_data.to_excel(writer, sheet_name='ChartData', index=False)

        # Configure the chart
        chart1.add_series({
            'name': 'Marginal Reach (%)',
            'categories': '=ChartData!$A$2:$A$' + str(len(best_combo) + 1),
            'values': '=ChartData!$B$2:$B$' + str(len(best_combo) + 1),
        })

        chart1.add_series({
            'name': 'Incremental Reach (%)',
            'categories': '=ChartData!$A$2:$A$' + str(len(best_combo) + 1),
            'values': '=ChartData!$C$2:$C$' + str(len(best_combo) + 1),
        })

        # Add line series for cumulative reach
        chart1.add_series({
            'name': 'Cumulative Reach (%)',
            'categories': '=ChartData!$A$2:$A$' + str(len(best_combo) + 1),
            'values': '=ChartData!$D$2:$D$' + str(len(best_combo) + 1),
            'type': 'line',
            'marker': {'type': 'automatic'},
            'line': {'color': 'red', 'width': 2},
        })

        # Configure chart layout
        chart1.set_title({'name': 'Reach Analysis by Feature'})
        chart1.set_x_axis({'name': 'Features'})
        chart1.set_y_axis({'name': 'Reach Percentage (%)'})
        chart1.set_size({'width': 720, 'height': 400})

        # Insert chart into the chart sheet
        chart_sheet.insert_chart('B2', chart1)

        # Add raw data sheet
        df.to_excel(writer, sheet_name='Raw Data', index=True)

        # Set column widths
        for sheet in workbook.worksheets():
            sheet.set_column('A:Z', 15)  # Set width for all columns

    # Prepare the Excel file for download
    output.seek(0)
    return output

def main():
    st.title("📊 TURF Analysis Tool")
    st.markdown("""
    This tool performs TURF (Total Unduplicated Reach and Frequency) analysis to help optimize 
    feature selection and maximize reach across your target audience.

    Upload a CSV file where:
    - Each row represents a potential customer
    - Each column represents a feature
    - Values are binary (0/1 or True/False) indicating if that customer is reached by the feature
    - First row should contain feature names
    - Any index column will be automatically ignored
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
                "Upload your respondent data (CSV)",
                type=['csv'],
                help="CSV should have binary values (0/1 or True/False) for each feature"
            )
            if uploaded_file:
                try:
                    # Read CSV with pandas, ignore index column if present
                    df = pd.read_csv(uploaded_file, index_col=0)
                    if validate_data(df):
                        st.success("Data loaded successfully!")
                        st.write("Data Preview:")
                        st.write(df.head(3))
                        st.info(f"Loaded {len(df)} respondents and {len(df.columns)} features")
                    else:
                        st.error("Invalid data format. Please ensure all values are binary (0/1 or True/False).")
                        return
                except Exception as e:
                    # Try reading without index column
                    try:
                        df = pd.read_csv(uploaded_file)
                        if validate_data(df):
                            st.success("Data loaded successfully!")
                            st.write("Data Preview:")
                            st.write(df.head(3))
                            st.info(f"Loaded {len(df)} respondents and {len(df.columns)} features")
                        else:
                            st.error("Invalid data format. Please ensure all values are binary (0/1 or True/False).")
                            return
                    except Exception as e:
                        st.error(f"Error reading file: {str(e)}")
                        return
        else:
            df = create_sample_data()
            st.info("Sample data loaded!")
            st.write("Preview of sample data:")
            st.write(df.head(3))

    # Feature selection
    if 'df' in locals():
        st.header("Feature Selection")
        col1, col2 = st.columns([2, 1])

        # Get feature reach information
        feature_reach = df.sum().sort_values(ascending=False)
        feature_reach_pct = (feature_reach / len(df) * 100).round(1)

        # Display feature reach information
        st.subheader("Feature Reach Overview")
        reach_df = pd.DataFrame({
            'Feature': feature_reach.index,
            'Respondents Reached': feature_reach.values,
            'Reach %': feature_reach_pct.values
        })
        st.dataframe(reach_df)

        with col1:
            default_features = get_top_features(df, n=min(5, len(df.columns)))
            selected_features = st.multiselect(
                "Select features to include in analysis:",
                options=feature_reach.index.tolist(),  # Show features sorted by reach
                default=default_features,
                help="Features are sorted by total reach. Top features are selected by default."
            )

        with col2:
            # Calculate maximum allowed combinations
            max_allowed = len(selected_features)
            suggested_max = min(5, max_allowed)  # Default suggestion of 5 or less

            max_combinations = st.number_input(
                "Maximum number of features to combine:",
                min_value=1,
                max_value=max_allowed if selected_features else 1,
                value=suggested_max if selected_features else 1,
                help="Select how many features to combine. Higher numbers will take longer to analyze."
            )

            # Add warning for large combinations
            if max_combinations > 5:
                st.warning(
                    "Analyzing many combinations may take longer. "
                    "Consider starting with fewer combinations first."
                )

        if st.button("Run TURF Analysis", type="primary"):
            if len(selected_features) < 1:
                st.warning("Please select at least one feature.")
                return

            # Show progress message for larger analyses
            if max_combinations > 3:
                progress_msg = st.info("Analyzing combinations... This may take a moment.")

            # Perform TURF analysis
            analyzer = TURFAnalyzer(df[selected_features])
            results = analyzer.analyze(max_combinations)

            # Display results
            st.header("Analysis Results")

            # Best combination details
            best_combo = results['best_combination']
            total_reach = results['max_reach']
            total_respondents = results['total_respondents']
            reach_percentage = (total_reach / total_respondents) * 100

            st.subheader("Best Feature Combination")
            st.markdown(f"""
            - **Selected Features:** {', '.join(best_combo)}
            - **Total Reach:** {total_reach:,.0f} respondents ({reach_percentage:.1f}% of total)
            - **Total Respondents:** {total_respondents:,.0f}
            """)

            # Create reach contribution chart
            individual_reaches = []
            for feature in best_combo:
                feature_reach = df[feature].sum()
                reach_pct = (feature_reach / total_respondents) * 100
                individual_reaches.append({
                    'Feature': feature,
                    'Respondents Reached': feature_reach,
                    'Reach Percentage': reach_pct
                })

            reach_data = pd.DataFrame(individual_reaches)

            fig = px.bar(
                reach_data,
                x='Feature',
                y='Reach Percentage',
                title='Individual Feature Reach in Best Combination',
                color='Feature',
                text=reach_data['Reach Percentage'].round(1).astype(str) + '%'
            )
            fig.update_layout(showlegend=False)
            st.plotly_chart(fig, use_container_width=True)


            # Create reach metrics table
            reach_metrics = []
            cumulative_reach = 0
            previous_reach = 0

            for i, feature in enumerate(best_combo):
                current_combo = best_combo[:i+1]
                feature_reach = df[feature].sum()
                reach_pct = (feature_reach / total_respondents) * 100

                current_total_reach = results['incremental_reach'][i]
                incremental_reach = current_total_reach - previous_reach
                incremental_pct = (incremental_reach / total_respondents) * 100

                reach_metrics.append({
                    'Feature': feature,
                    'Marginal Reach': f"{feature_reach:,.0f} ({reach_pct:.1f}%)",
                    'Incremental Reach': f"{incremental_reach:,.0f} ({incremental_pct:.1f}%)",
                    'Cumulative Reach': f"{current_total_reach:,.0f} ({results['reach_percentages'][i]:.1f}%)"
                })

                previous_reach = current_total_reach

            # Display metrics table
            st.subheader("Detailed Reach Metrics")
            st.markdown("""
            - **Marginal Reach**: Number of respondents reached by each feature individually
            - **Incremental Reach**: Additional respondents reached by adding each feature
            - **Cumulative Reach**: Total respondents reached up to and including each feature
            """)
            reach_metrics_df = pd.DataFrame(reach_metrics)
            st.table(reach_metrics_df)

            # Create enhanced reach visualization
            st.subheader("Reach Analysis Visualization")

            # Prepare data for visualization
            viz_data = pd.DataFrame(reach_metrics)
            viz_data[['Marginal Count', 'Marginal Pct']] = viz_data['Marginal Reach'].str.extract(r'(\d+,?\d*) \(([\d.]+)%\)')
            viz_data[['Incremental Count', 'Incremental Pct']] = viz_data['Incremental Reach'].str.extract(r'(\d+,?\d*) \(([\d.]+)%\)')
            viz_data[['Cumulative Count', 'Cumulative Pct']] = viz_data['Cumulative Reach'].str.extract(r'(\d+,?\d*) \(([\d.]+)%\)')

            # Convert percentage strings to float
            viz_data['Marginal Pct'] = viz_data['Marginal Pct'].astype(float)
            viz_data['Incremental Pct'] = viz_data['Incremental Pct'].astype(float)
            viz_data['Cumulative Pct'] = viz_data['Cumulative Pct'].astype(float)

            # Create figure with secondary y-axis
            fig = go.Figure()

            # Add bars for marginal reach
            fig.add_trace(go.Bar(
                name='Marginal Reach',
                x=viz_data['Feature'],
                y=viz_data['Marginal Pct'],
                text=viz_data['Marginal Pct'].round(1).astype(str) + '%',
                textposition='auto',
            ))

            # Add bars for incremental reach
            fig.add_trace(go.Bar(
                name='Incremental Reach',
                x=viz_data['Feature'],
                y=viz_data['Incremental Pct'],
                text=viz_data['Incremental Pct'].round(1).astype(str) + '%',
                textposition='auto',
            ))

            # Add line for cumulative reach
            fig.add_trace(go.Scatter(
                name='Cumulative Reach',
                x=viz_data['Feature'],
                y=viz_data['Cumulative Pct'],
                mode='lines+markers+text',
                text=viz_data['Cumulative Pct'].round(1).astype(str) + '%',
                textposition='top center',
                line=dict(color='red', width=2),
                yaxis='y2'
            ))

            # Update layout
            fig.update_layout(
                title='Reach Analysis by Feature',
                xaxis_title='Features',
                yaxis_title='Reach Percentage (%)',
                barmode='group',
                yaxis2=dict(
                    title='Cumulative Reach (%)',
                    overlaying='y',
                    side='right'
                ),
                yaxis=dict(range=[0, 100]),
                yaxis2_range=[0, 100],
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1
                )
            )

            st.plotly_chart(fig, use_container_width=True)

            # Display incremental reach
            st.subheader("Incremental Reach Analysis")
            incremental_data = pd.DataFrame({
                'Features': [' + '.join(best_combo[:i+1]) for i in range(len(best_combo))],
                'Cumulative Reach %': results['reach_percentages']
            })

            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=incremental_data['Features'],
                y=incremental_data['Cumulative Reach %'],
                mode='lines+markers+text',
                text=incremental_data['Cumulative Reach %'].round(1).astype(str) + '%',
                textposition='top center',
                name='Cumulative Reach'
            ))
            fig.update_layout(
                title='Cumulative Reach by Feature Addition',
                xaxis_title='Features Added',
                yaxis_title='Cumulative Reach (%)',
                yaxis_range=[0, 100]
            )
            st.plotly_chart(fig, use_container_width=True)

            # Download results
            results_df = pd.DataFrame({
                'Metric': ['Best Combination', 'Total Reach', 'Reach Percentage', 'Total Respondents'],
                'Value': [
                    ', '.join(best_combo),
                    f"{total_reach:,.0f}",
                    f"{reach_percentage:.1f}%",
                    f"{total_respondents:,.0f}"
                ]
            })

            # Download buttons
            col1, col2 = st.columns(2)

            with col1:
                csv = results_df.to_csv(index=False)
                st.download_button(
                    label="Download Summary (CSV)",
                    data=csv,
                    file_name="turf_analysis_summary.csv",
                    mime="text/csv"
                )

            with col2:
                excel_file = create_excel_report(
                    results=results,
                    df=df,
                    best_combo=best_combo,
                    reach_metrics_df=reach_metrics_df,
                    viz_data=viz_data
                )

                st.download_button(
                    label="Download Full Report (Excel)",
                    data=excel_file,
                    file_name=f"turf_analysis_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

            if max_combinations > 3:
                progress_msg.empty()

if __name__ == "__main__":
    main()