import base64
import datetime
import io
import pandas as pd
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import dash
from dash.dependencies import Input, Output, State
import dash_core_components as dcc
import dash_html_components as html
import dash_table
from textblob import TextBlob
import re
import pandas as pd
import plotly.express as px

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
server = app.server

app.config.suppress_callback_exceptions=True

app.layout = html.Div([
    dcc.Upload(
        id='upload-data',
        children=html.Div([
            'Drag and Drop or ',
            html.A('Select Files')
        ]),
        style={
            'width': '100%',
            'height': '60px',
            'lineHeight': '60px',
            'borderWidth': '1px',
            'borderStyle': 'dashed',
            'borderRadius': '5px',
            'textAlign': 'center',
            'margin': '10px'
        },
        # Allow multiple files to be uploaded
        multiple=True
    ),
    html.Div(id='output-div'),
    html.Div(id='output-data-upload'),
])


def parse_contents(contents, filename, date):
    content_type, content_string = contents.split(',')

    decoded = base64.b64decode(content_string)
   # try:
    if 'csv' in filename:
            # Assume that the user uploaded a CSV file
            data = pd.read_csv(
                io.StringIO(decoded.decode('utf-8')))

            def clean(text):
                # Removes all special characters and numericals leaving the alphabets
                text = re.sub('[^A-Za-z]+', ' ', text)
                return text

    elif 'xls' in filename:
        # Assume that the user uploaded an excel file
          df = pd.read_excel(io.BytesIO(decoded))



    #except Exception as e:
    #    print(e)
    #    return html.Div([
    #        'There was an error processing this file.!!!!!!!!!!!!!!!!!!!!!!!!'
    #    ])

    return html.Div([
        html.H6('Choose a textual variable for feedback ranking'),
        #html.p('Select a textual variable'),
        dcc.Dropdown(id = 'Variables', options=[{'label':x, 'value':x } for x in data.columns ]),
        html.Button(id="submit-button", children="Generate data"),
       # html.P("Inset Y axis data"),

        html.Hr(),

        dash_table.DataTable(
            data=data.to_dict('records'),
            columns=[{'name': i, 'id': i} for i in data.columns],
            style_cell={
                "textAlign": 'left',
            },
            style_header = {
             'fontWeight':'bold',
             'backgroundColor' : 'rgb(230,230,100)'
            }

        ),
        dcc.Store(id='stored-data', data=data.to_dict('dict')),
        html.Hr(),  # horizontal line

        # # For debugging, display the raw contents provided by the web browser
        # html.Div('Raw Content'),
        # html.Pre(contents[0:200] + '...', style={
        #     'whiteSpace': 'pre-wrap',
        #     'wordBreak': 'break-all'
        # })
    ] )


@app.callback(Output(component_id='output-data-upload', component_property='children'),
              [Input(component_id='upload-data', component_property='contents')],
              [State(component_id='upload-data', component_property='filename'),
               State(component_id='upload-data', component_property='last_modified')])
def update_output(list_of_contents, list_of_names, list_of_dates):
    if list_of_contents is not None:
        if 'csv' not in list_of_names[0]:
            return html.Div(['There was an error processing this file.'])

        children = [
            parse_contents(c, n, d) for c, n, d in
            zip(list_of_contents, list_of_names, list_of_dates)]
        return children


@app.callback(Output(component_id='output-div', component_property='children'),
              [Input(component_id='submit-button', component_property='n_clicks')],
              [State(component_id='stored-data', component_property='data'),
               State(component_id='Variables', component_property='value')])
#
def make_graphs(n, data, Variables):
    if n is None:
        return dash.no_update
    else:

        def clean(text):
            # Removes all special characters and numericals leaving the alphabets
            text = re.sub('[^A-Za-z]+', ' ', str(text))
            return text
            # function to calculate subjectivity

        def getSubjectivity(CleanedReviews):
            return TextBlob(CleanedReviews).sentiment.subjectivity
            # function to calculate polarity

        def getPolarity(CleanedReviews):
            return TextBlob(CleanedReviews).sentiment.polarity

            # function to analyze the reviews

        def analysis(score):
            if score < 0:
                return 'Negative'
            elif score == 0:
                return 'Neutral'
            else:
                return 'Positive'

        df = pd.DataFrame.from_dict(data)
        df = pd.DataFrame(df)
        #df = df.to_json()
        df[str(Variables)] = df[str(Variables)].astype(str)

        # fin_data['CleanedReviews'] = df['reviewText'].apply(clean)
        df[str(Variables)] = df[str(Variables)].apply(clean)
        fin_data = pd.DataFrame(df[[str(Variables)]])
        fin_data['Subjectivity'] = round(fin_data[str(Variables)].apply(getSubjectivity),3)
        fin_data['Positivity'] = round(fin_data[str(Variables)].apply(getPolarity),3)
        fin_data['Analysis'] = fin_data['Positivity'].apply(analysis)
        cols = fin_data.columns.tolist()
        cols = cols[-1:] + cols[:-1]
        cols = cols[-1:] + cols[:-1]
        cols = cols[-1:] + cols[:-1]
        fin_data = fin_data[cols]
        fin_data = fin_data.sort_values("Positivity")

        textdata = dash_table.DataTable(
            data=fin_data.to_dict('records'),
            columns=[{'name': i, 'id': i} for i in fin_data.columns],
            style_cell={
                "textAlign": 'left',
            },
            style_header = {
             'fontWeight':'bold',
             'backgroundColor' : 'rgb(230,230,100)'
            }

        )
        textdata
        return  [html.H6('The data below is ranked by the positivity of the chosen variable. From the most negative to the most positive'),textdata]


if __name__ == '__main__':
    app.run_server(debug=True)
