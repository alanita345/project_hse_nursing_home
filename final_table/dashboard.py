import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from dash import Dash, dcc, html, Input, Output
from collections import Counter
import re

df = pd.read_csv(r'D:\hsenespr\project_hse_nursing_home\final_table\all_pansionaty_combined.csv', encoding='utf-8-sig')

df['rating'] = pd.to_numeric(df['rating'], errors='coerce')
df['reviews'] = pd.to_numeric(df['reviews'], errors='coerce').fillna(0)
df['positive_words'] = pd.to_numeric(df['positive_words'], errors='coerce').fillna(0)
df['negative_words'] = pd.to_numeric(df['negative_words'], errors='coerce').fillna(0)
df['price'] = pd.to_numeric(df['price'], errors='coerce')
df['sentiment_score'] = df['positive_words'] - df['negative_words']
df['lat'] = pd.to_numeric(df['lat'], errors='coerce')
df['lon'] = pd.to_numeric(df['lon'], errors='coerce')

def get_segment(rating):
    if rating >= 4.7:
        return 'Отлично (4.7-5.0)'
    elif rating >= 4.0:
        return 'Хорошо (4.0-4.7)'
    elif rating >= 3.0:
        return 'Средне (3.0-4.0)'
    elif rating > 0:
        return 'Плохо (<3.0)'
    return 'Нет рейтинга'

df['segment'] = df['rating'].apply(get_segment)

all_services = ' | '.join(df[df['services'] != '']['services'].dropna().tolist())
service_list = [s.strip() for s in all_services.split('|') if s.strip()]
service_counts = Counter(service_list)
services_df = pd.DataFrame(service_counts.most_common(20), columns=['Услуга', 'Количество'])

map_data = df[(df['rating'] > 4.5) & (df['lat'].notna()) & (df['lon'].notna())].copy()

df['services_count'] = df['services'].apply(lambda x: len(str(x).split('|')) if pd.notna(x) and x != '' else 0)

app = Dash(__name__)

app.layout = html.Div([
    html.H1("Анализ рынка пансионатов для пожилых", 
            style={'textAlign': 'center', 'color': '#2c3e50', 'padding': '20px'}),
    
    html.Div([
        html.Div([dcc.Graph(id='rating-dist')], className='six columns'),
        html.Div([dcc.Graph(id='top-popular')], className='six columns'),
    ], className='row', style={'padding': '10px'}),
    
    html.Div([
        html.Div([dcc.Graph(id='price-rating')], className='six columns'),
        html.Div([dcc.Graph(id='price-dist')], className='six columns'),
    ], className='row', style={'padding': '10px'}),
    
    html.Div([
        html.Div([dcc.Graph(id='segments')], className='six columns'),
        html.Div([dcc.Graph(id='map')], className='six columns'),
    ], className='row', style={'padding': '10px'}),
    
    html.Div([
        html.Div([dcc.Graph(id='words-rating')], className='six columns'),
        html.Div([dcc.Graph(id='services-top')], className='six columns'),
    ], className='row', style={'padding': '10px'}),

    html.Div([
        html.Div([dcc.Graph(id='source-rating')], className='six columns'),
        html.Div([dcc.Graph(id='price-available')], className='six columns'),
    ], className='row', style={'padding': '10px'}),
    
    html.Div([
        html.Div([dcc.Graph(id='reviews-dist')], className='six columns'),
    ], className='row', style={'padding': '10px'}),
])


@app.callback(Output('rating-dist', 'figure'), Input('rating-dist', 'id'))
def update_rating_dist(_):
    rating_data = df[df['rating'].notna() & (df['rating'] > 0)]
    fig = px.histogram(rating_data, x='rating', nbins=30,
                       title='Распределение рейтингов',
                       labels={'rating': 'Рейтинг', 'count': 'Количество'},
                       color_discrete_sequence=['#2ecc71'])
    fig.update_layout(template='plotly_white', height=400)
    return fig

@app.callback(Output('top-popular', 'figure'), Input('top-popular', 'id'))
def update_top_popular(_):
    top_data = df.nlargest(20, 'reviews')[df['reviews'] > 0]
    fig = px.bar(top_data[::-1], x='reviews', y='name', orientation='h',
                 title='Топ-20 по популярности (отзывам)',
                 labels={'reviews': 'Количество отзывов', 'name': 'Название'},
                 color='rating', color_continuous_scale='Viridis',
                 hover_data=['source'])
    fig.update_layout(template='plotly_white', height=500)
    return fig

@app.callback(Output('price-rating', 'figure'), Input('price-rating', 'id'))
def update_price_rating(_):
    price_data = df[df['price'].notna() & (df['price'] > 0) & df['rating'].notna() & (df['rating'] > 0)]
    fig = px.scatter(price_data, x='price', y='rating', 
                     title='Зависимость цены от рейтинга',
                     labels={'price': 'Цена (руб/день)', 'rating': 'Рейтинг'},
                     hover_data=['name', 'source', 'reviews'],
                     color='rating', color_continuous_scale='Viridis',
                     size='reviews', size_max=30)
    fig.update_layout(template='plotly_white', height=400)
    return fig

@app.callback(Output('price-dist', 'figure'), Input('price-dist', 'id'))
def update_price_dist(_):
    price_data = df[df['price'].notna() & (df['price'] > 0)]
    fig = px.histogram(price_data, x='price', nbins=30,
                       title='Распределение цен',
                       labels={'price': 'Цена (руб/день)', 'count': 'Количество'},
                       color_discrete_sequence=['#3498db'])
    if len(price_data) > 0:
        fig.add_vline(x=price_data['price'].median(), line_dash="dash", line_color="red",
                      annotation_text=f"Медиана: {price_data['price'].median():.0f} руб")
    fig.update_layout(template='plotly_white', height=400)
    return fig

@app.callback(Output('segments', 'figure'), Input('segments', 'id'))
def update_segments(_):
    segment_counts = df['segment'].value_counts().reset_index()
    segment_counts.columns = ['segment', 'count']
    fig = px.bar(segment_counts, x='segment', y='count',
                 title='Количество пансионатов по сегментам',
                 labels={'segment': 'Сегмент', 'count': 'Количество'},
                 color='segment',
                 color_discrete_sequence=['#e74c3c', '#f39c12', '#3498db', '#2ecc71', '#95a5a6'])
    fig.update_layout(template='plotly_white', height=400, showlegend=False)
    return fig

@app.callback(Output('map', 'figure'), Input('map', 'id'))
def update_map(_):
    if len(map_data) == 0:
        fig = go.Figure()
        fig.add_annotation(text="Нет данных для карты", xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False)
        fig.update_layout(title='Лучшие пансионаты (рейтинг > 4.5)', height=400)
        return fig
    fig = px.scatter_mapbox(map_data, lat='lat', lon='lon', hover_name='name', 
                            hover_data={'rating': True, 'reviews': True},
                            color='rating', size='reviews',
                            color_continuous_scale='Viridis', zoom=9, height=400,
                            title=f'Лучшие пансионаты — {len(map_data)} мест')
    fig.update_layout(mapbox_style="open-street-map")
    return fig

@app.callback(Output('words-rating', 'figure'), Input('words-rating', 'id'))
def update_words_rating(_):
    words_data = df[df['rating'].notna() & (df['rating'] > 0)]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=words_data['rating'], y=words_data['positive_words'],
                             mode='markers', name='Положительные слова', marker=dict(color='#2ecc71', size=8)))
    fig.add_trace(go.Scatter(x=words_data['rating'], y=words_data['negative_words'],
                             mode='markers', name='Отрицательные слова', marker=dict(color='#e74c3c', size=8)))
    fig.update_layout(title='Тональность отзывов от рейтинга',
                      xaxis_title='Рейтинг', yaxis_title='Количество слов',
                      template='plotly_white', height=400)
    return fig

@app.callback(Output('services-top', 'figure'), Input('services-top', 'id'))
def update_services(_):
    fig = px.bar(services_df.head(15), x='Количество', y='Услуга', orientation='h',
                 title='Топ-15 услуг', labels={'Количество': 'Упоминаний'},
                 color='Количество', color_continuous_scale='Oranges')
    fig.update_layout(template='plotly_white', height=400)
    return fig

@app.callback(Output('source-rating', 'figure'), Input('source-rating', 'id'))
def update_source_rating(_):
    source_data = df[df['rating'] > 0].groupby('source')['rating'].mean().reset_index()
    fig = px.bar(source_data, x='source', y='rating', 
                 title='Средний рейтинг по источникам',
                 color='source', color_discrete_sequence=['#2ecc71', '#3498db', '#e74c3c'])
    fig.update_layout(template='plotly_white', height=400)
    return fig

@app.callback(Output('price-available', 'figure'), Input('price-available', 'id'))
def update_price_available(_):
    has_price = df['price'].notna().sum()
    no_price = len(df) - has_price
    fig = go.Figure(data=[go.Pie(labels=['Есть цена', 'Нет цены'], 
                                  values=[has_price, no_price],
                                  marker_colors=['#2ecc71', '#e74c3c'])])
    fig.update_layout(title='Наличие цен в карточках', height=400)
    return fig

@app.callback(Output('reviews-dist', 'figure'), Input('reviews-dist', 'id'))
def update_reviews_dist(_):
    reviews_data = df[df['reviews'] > 0]['reviews']
    fig = px.histogram(reviews_data, x='reviews', nbins=30,
                       title='Распределение количества отзывов',
                       labels={'reviews': 'Количество отзывов', 'count': 'Количество пансионатов'},
                       color_discrete_sequence=['#9b59b6'])
    fig.update_layout(template='plotly_white', height=400)
    return fig




if __name__ == '__main__':
    print(f"Загружено {len(df)} пансионатов")
    print(f"На карте: {len(map_data)} точек")
    print("Откройте в браузере: http://127.0.0.1:8050")
    
    app.run(debug=True, port=8050)