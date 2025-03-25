import plotly.graph_objects as go
import pandas as pd
import numpy as np
from calendar import month_abbr, month_name
import plotly.express as px


#================= Traitement des données ================#
df = pd.read_csv("data.csv", index_col=0)
df = df[['CustomerID', 'Gender', 'Location', 'Product_Category', 'Quantity', 'Avg_Price', 'Transaction_Date', 'Month', 'Discount_pct']]

df['CustomerID'] = df['CustomerID'].fillna(0).astype(int)
df['Transaction_Date'] = pd.to_datetime(df['Transaction_Date'])

df['Total_price'] = df['Quantity'] * df['Avg_Price'] * (1 - (df['Discount_pct'] / 100)).round(3)

def calculer_chiffre_affaire(data):
    return data['Total_price'].sum()

def frequence_meilleure_vente(data, top=10, ascending=False):
    resultat = pd.crosstab(
        [data['Gender'], data['Product_Category']], 
        'Total vente', 
        values=data['Total_price'], 
        aggfunc= lambda x : len(x), 
        rownames=['Sexe', 'Categorie du produit'],
        colnames=['']
    ).reset_index().groupby(
        ['Sexe'], as_index=False, group_keys=True
    ).apply(
        lambda x: x.sort_values('Total vente', ascending=ascending).iloc[:top, :]
    ).reset_index(drop=True).set_index(['Sexe', 'Categorie du produit'])

    return resultat

def indicateur_du_mois(data, current_month = 12, freq=True, abbr=False): 
    previous_month = current_month - 1 if current_month > 1 else 12
    if freq : 
        resultat = data['Month'][(data['Month'] == current_month) | (data['Month'] == previous_month)].value_counts()
        # sort by index
        resultat = resultat.sort_index()
        resultat.index = [(month_abbr[i] if abbr else month_name[i]) for i in resultat.index]
        return resultat
    else:
        resultat = data[(data['Month'] == current_month) | (data['Month'] == previous_month)].groupby('Month').apply(calculer_chiffre_affaire)
        resultat.index = [(month_abbr[i] if abbr else month_name[i]) for i in resultat.index]
        return resultat

def barplot_top_10_ventes(data) :
    df_plot = frequence_meilleure_vente(data, ascending=True)
    graph = px.bar(
        df_plot,
        x='Total vente', 
        y=df_plot.index.get_level_values(1),
        color=df_plot.index.get_level_values(0), 
        barmode='group',
        title="Frequence des 10 meilleures ventes",
        labels={"x": "Fréquence", "y": "Categorie du produit", "color": "Sexe"},
        width=600, height=600
    ).update_layout(
        margin = dict(t=60)
    )
    return graph

# Evolution chiffre d'affaire
def plot_evolution_chiffre_affaire(data) :
    df_plot = data.groupby(pd.Grouper(key='Transaction_Date', freq='W')).apply(calculer_chiffre_affaire)[:-1]
    chiffre_evolution = px.line(
        x=df_plot.index, y=df_plot,
        title="Evolution du chiffre d'affaire par semaine",
        labels={"x": "Semaine", "y": "Chiffre d'affaire"},
    ).update_layout( 
        width=900, height=400,
        margin=dict(t=60, b=0),
        
    )
    return chiffre_evolution

## Chiffre d'affaire du mois
def plot_chiffre_affaire_mois(data) :
    df_plot = indicateur_du_mois(data, freq=False)
    indicateur = go.Figure(
        go.Indicator(
            mode = "number+delta",
            value = df_plot[1],
            delta = {'reference': df_plot[0]},
            domain = {'row': 0, 'column': 1},
            title=f"{df_plot.index[1]}",
        )
    ).update_layout(
        width=200, height=200, 
        margin=dict(l=0, r=10, t=10, b=0)
    )
    return indicateur

# Ventes du mois
def plot_vente_mois(data, abbr=False) :
    df_plot = indicateur_du_mois(data, freq=True, abbr=abbr)
    indicateur = go.Figure(
        go.Indicator(
            mode = "number+delta",
            value = df_plot[1],
            delta = {'reference': df_plot[0]},
            domain = {'row': 0, 'column': 1},
            title=f"{df_plot.index[1]}",
        )
    ).update_layout( 
        width=200, height=200, 
        margin=dict(l=0, r=10, t=10, b=0)
    )
    return indicateur
    

import plotly.graph_objects as go
import pandas as pd
import numpy as np
import dash
from dash import dcc, html, Input, Output, callback
import dash_bootstrap_components as dbc
import dash_table
from dash import dash_table

#================= Traitement des données ================#
df = pd.read_csv("/Users/pierrequintindekercadio/Documents/Documents - Mac/Python avancé /data.csv", index_col=0)
df = df[['CustomerID', 'Gender', 'Location', 'Product_Category', 'Quantity', 'Avg_Price', 'Transaction_Date', 'Month', 'Discount_pct']]

df['CustomerID'] = df['CustomerID'].fillna(0).astype(int)
df['Transaction_Date'] = pd.to_datetime(df['Transaction_Date'])
df['Total_price'] = df['Quantity'] * df['Avg_Price'] * (1 - (df['Discount_pct'] / 100)).round(3)

city_options = [
    {'label': 'Toutes les villes', 'value': 'all'},
    {'label': 'Chicago', 'value': 'Chicago'},
    {'label': 'California', 'value': 'California'},
    {'label': 'New York', 'value': 'New York'},
    {'label': 'New Jersey', 'value': 'New Jersey'},
    {'label': 'Washington DC', 'value': 'Washington DC'}
]

def filter_by_city(df, selected_city):
    """
    Filtre les données en fonction de la ville sélectionnée.
    - Si 'Toutes les villes' est sélectionné, retourne toutes les données.
    - Sinon, filtre selon la ville choisie.
    """
    if selected_city == "all":
        return df 
    else:
        return df[df["Location"] == selected_city]


app = dash.Dash(external_stylesheets=[dbc.themes.BOOTSTRAP])

app.layout = dbc.Container([
  
    dbc.Row([
        dbc.Col(
             html.H3("ECAP STORE", className="text-left", style={"fontSize": "30px", "color": "black", "fontWeight": "bold"}),
            md=6,
            style={
                "height": "7vh",
                "display": "flex",
                "alignItems": "center",
                "justifyContent": "flex-start",
                "backgroundColor": "#ADD8E6",  
                "paddingLeft": "15px",
                "fontWeight": "bold"
            },
        ),
        dbc.Col(
            dcc.Dropdown(
                id="city-select",
                options=city_options,
                value="all", 
                placeholder="Choisissez des zones",
                style={
                    "fontSize": "16px",
                    "height": "40px",
                    "width": "80%",
                    "borderRadius": "50px",
                }
            ),
            md=6,
            style={
                "height": "7vh",
                "display": "flex",
                "alignItems": "center",
                "justifyContent": "center",
                "backgroundColor": "#ADD8E6",
                "padding": "0px 15px",
            },
        ),
    ], style={"marginBottom": "10px"}),


    dbc.Row([
        dbc.Col([
            # Indicateurs centrés
            dbc.Row([
                dbc.Col(dcc.Graph(id='chiffre-affaire-mois'), md=5, style={"min-height": "100px", "textAlign": "center"}, className="p-2"),
                dbc.Col(dcc.Graph(id='ventes-mois'), md=5, style={"min-height": "100px", "textAlign": "center"}, className="p-2"),
            ], justify="center"),

            # Graphique des meilleures ventes
            dbc.Row([
                dbc.Col(dcc.Graph(id='top-ventes'), md=12, style={"min-height": "400px"}, className="p-3"),
            ]),
        ], md=5),

        # Colonne de droite
        dbc.Col([
            dbc.Row([
                dbc.Col(dcc.Graph(id='evolution-ca'), md=10, style={"min-height": "300px"}, className="p-3"),
            ]),

            dbc.Row([
                dbc.Col(dash_table.DataTable(
                    id='table-ventes',
                    columns=[
                        {'name': 'Date', 'id': 'Transaction_Date'},
                        {'name': 'Gender', 'id': 'Gender'},
                        {'name': 'Location', 'id': 'Location'},
                        {'name': 'Product Category', 'id': 'Product_Category'},
                        {'name': 'Quantity', 'id': 'Quantity'},
                        {'name': 'Avg Price', 'id': 'Avg_Price'},
                        {'name': 'Discount Pct', 'id': 'Discount_pct'}
                    ],
                    data=df.to_dict('records')[:100],  
                    page_size=10,
                    style_table={'overflowX': 'auto', 'minWidth': '100%'},
                    style_header={'backgroundColor': 'lightgrey', 'fontWeight': 'bold'},
                    filter_action='native',
                    sort_action='native',
                    style_cell={'textAlign': 'left', 'fontSize': '12px', 'padding': '8px'}
                ), md=12, style={"min-height": "100px"}, className="p-3"),
            ]),
        ], md=7),
    ], justify="center"), 

], fluid=True)


@callback(
    [
        Output('chiffre-affaire-mois', 'figure'),
        Output('ventes-mois', 'figure'),
        Output('top-ventes', 'figure'),
        Output('evolution-ca', 'figure'),
        Output('table-ventes', 'data')
    ],
    Input('city-select', 'value')
)
def update_content(selected_value):
    filtered_df = filter_by_city(df, selected_value) 
    
    return (
        plot_chiffre_affaire_mois(filtered_df),
        plot_vente_mois(filtered_df),
        barplot_top_10_ventes(filtered_df),
        plot_evolution_chiffre_affaire(filtered_df),
        filtered_df.assign(Transaction_Date=filtered_df['Transaction_Date'].dt.strftime('%Y-%m-%d')).to_dict('records')[:100]
    )

server = app.server

if __name__ == '__main__':
    app.run_server(debug=False, host = "0.0.0.0", port=8055)