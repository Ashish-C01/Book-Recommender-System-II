from dash import Dash, html, dcc, Output, Input, State, callback_context
import dash_bootstrap_components as dbc
import pandas as pd
import numpy as np
import requests
from dotenv import load_dotenv
import os

load_dotenv()

token = os.environ.get('token')

pt_table = pd.read_pickle('user book data.pkl')
book_details = pd.read_pickle('book details.pkl')
with open('similarity score.npy', 'rb') as f:
    similarity_score = np.load(f)
book_names = pt_table.index.values.tolist()


def recommend(book_name):
    book_index = np.where(pt_table.index == book_name)[0][0]
    distances = similarity_score[book_index]
    similar_items = sorted(list(enumerate(distances)),
                           key=lambda x: x[1], reverse=True)[1:7]
    suggestion = []
    for i in similar_items:
        suggestion.append(pt_table.index[i[0]])
    return suggestion


def get_book_details(book_name):
    response = requests.get(
        f'https://www.googleapis.com/books/v1/volumes?q={book_name}&maxResults=1&orderBy=relevance&key={token}')
    if response.status_code == 200:
        body = response.json()
        if body['totalItems']:
            desc = body['items'][0]['volumeInfo']
            description = desc.get('description', "Not Found")
            categories = ", ".join(
                desc.get('categories', ["Not Found"]))
            preview_link = desc.get('previewLink', "Not Found")
            return [description, categories, preview_link]
    return ["Not Found", "Not Found", "Not Found"]


def generate_card(image_url, book_title, extra_book_details, c_id):
    collapsible_id = c_id
    return dbc.Card(
        [
            dbc.CardImg(src=image_url, top=True,
                        style={'width': '150px', 'height': '200px', 'align-self': 'center', 'margin-top': '10%'}),
            dbc.CardBody(
                [
                    html.H5(book_title, className="card-title", style={'text-align': 'center'}),
                    dbc.Button("More Details", id=f"toggle-{c_id}", color="primary", className="mt-2",
                               n_clicks=0, style={'position': 'relative', 'left': '25%'}),
                    dbc.Collapse(
                        dbc.CardBody(
                            [
                                html.P([html.B('Description: '), f' {extra_book_details[0]}']),
                                html.P([html.B('Category: '), f' {extra_book_details[1]}']),
                                html.P([html.B('Preview Link: '), html.A(extra_book_details[2], href=extra_book_details[2], target="_blank")])
                            ]
                        ),
                        id=f'collapse-{collapsible_id}',
                        is_open=False,
                    )
                ]
            ),
        ],
        style={"width": "18rem"},
        className="m-2"
    )


app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.title = 'Book Recommender System'
app.layout = html.Div(style={"display": "flex", "flex-direction": "column", "align-items": "center", "justify-content": "center"},
    children=[html.H1(children='Book Recommender System', style={'textAlign': 'center'}),
    html.Div([
    dcc.Dropdown(book_names, '1984', id='dropdown-selection',style={'text-align': 'center'}),
    ],style={"width": "50%"}),
    dbc.Button("Recommend Books", id="recommend-button", color="primary", n_clicks=0, className="mt-2",
               style={'display': 'block', 'margin': 'auto'}),
    dcc.Loading(
    id="loading-spinner",
    type="circle",
    children=html.Div(id='card-container', className="d-flex flex-wrap justify-content-center"),
    fullscreen=True
    ),

]
)

@app.callback(
    Output('card-container', 'children'),
    [Input('recommend-button', 'n_clicks')],
    [State('dropdown-selection', 'value')]
)
def recommend_book(n_click, book_name):
    if n_click:
        recommendation = recommend(book_name)
        cards = []
        for ind, recom in enumerate(recommendation):
            extra_book_details = get_book_details(recom)
            cards.append(
                dbc.Col(generate_card(book_details[book_details['Book-Title'] == recom]['Image-URL-M'].values[0],
                                      f"{book_details[book_details['Book-Title'] == recom]['Book-Title'].values[0]} by {book_details[book_details['Book-Title'] == recom]['Book-Author'].values[0]}",
                                      extra_book_details, ind)))
        return [dbc.Row(cards[:3], justify="center"),
                dbc.Row(cards[3:], justify="center")]
    return html.Div()


for i in range(6):
    @app.callback(
        Output(f'collapse-{i}', 'is_open'),
        [Input(f'toggle-{i}', 'n_clicks')],
        [State(f'collapse-{i}', 'is_open')]
    )
    def toggle_collapse(n_clicks, is_open):
        ctx = callback_context
        if not ctx.triggered or n_clicks is None:
            return is_open

        return not is_open

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=7860)
