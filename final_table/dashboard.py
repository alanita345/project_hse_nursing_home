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
df['price'] = pd.to_numeric(df['price'], errors='coerce')
df['lat'] = pd.to_numeric(df['lat'], errors='coerce')
df['lon'] = pd.to_numeric(df['lon'], errors='coerce')

df.loc[df['price'] > 15000, 'price'] = None

def get_price_segment(price):
    if pd.isna(price) or price == 0:
        return 'Нет данных'
    elif price < 1500:
        return 'Эконом (до 1500)'
    elif price < 3000:
        return 'Средний (1500-3000)'
    elif price < 5000:
        return 'Комфорт (3000-5000)'
    return 'Премиум (5000+)'

df['price_segment'] = df['price'].apply(get_price_segment)

def get_rating_cat(rating):
    if pd.isna(rating):
        return 'Нет рейтинга'
    elif rating >= 4.7:
        return 'Отличный'
    elif rating >= 4.0:
        return 'Хороший'
    elif rating >= 3.0:
        return 'Средний'
    else:
        return 'Низкий'

df['rating_cat'] = df['rating'].apply(get_rating_cat)

all_services = ' | '.join(df[df['services'] != '']['services'].dropna().tolist())
service_list = [s.strip() for s in all_services.split('|') if s.strip()]
service_counts = Counter(service_list)
services_df = pd.DataFrame(service_counts.most_common(15), columns=['Услуга', 'Количество'])

map_data = df[df['lat'].notna() & df['lon'].notna()]

app = Dash(__name__)

app.layout = html.Div([
    html.H1("Анализ рынка пансионатов для пожилых", 
            style={'textAlign': 'center', 'color': '#2c3e50', 'padding': '20px'}),
    
    html.Div([
        dcc.Graph(id='rating-dist')
    ], className='row', style={'padding': '10px'}),
    
    html.Div([
        dcc.Graph(id='rating-reviews')
    ], className='row', style={'padding': '10px'}),
    
    html.Div([
        html.Div([dcc.Graph(id='price-segments')], className='six columns'),
        html.Div([dcc.Graph(id='map')], className='six columns'),
    ], className='row', style={'padding': '10px'}),
    
    html.Div([
        html.Div([dcc.Graph(id='top-rating')], className='six columns'),
        html.Div([dcc.Graph(id='top-services')], className='six columns'),
    ], className='row', style={'padding': '10px'}),
])


@app.callback(Output('rating-dist', 'figure'), Input('rating-dist', 'id'))
def update_rating_dist(_):
    rating_data = df[df['rating'].notna() & (df['rating'] > 0)]['rating']
    fig = go.Figure()
    fig.add_trace(go.Histogram(x=rating_data, nbinsx=25, marker_color='#2ecc71', opacity=0.9))
    fig.add_vline(x=rating_data.mean(), line_dash="dash", line_color="red", line_width=1.5,
                  annotation_text=f"Среднее: {rating_data.mean():.2f}")
    fig.update_layout(title='Распределение рейтингов пансионатов',
                      xaxis_title='Рейтинг', yaxis_title='Количество пансионатов',
                      template='plotly_white', height=400)
    return fig


@app.callback(Output('rating-reviews', 'figure'), Input('rating-reviews', 'id'))
def update_rating_reviews(_):
    data = df[df['rating'].notna() & (df['rating'] > 0) & (df['reviews'] > 0)]
    fig = px.scatter(data, x='reviews', y='rating', color='source',
                     title='Зависимость рейтинга от количества отзывов',
                     labels={'reviews': 'Количество отзывов', 'rating': 'Рейтинг'},
                     hover_data=['name', 'price'],
                     size='reviews', size_max=20,
                     color_discrete_sequence=['#2ecc71', '#3498db', '#e74c3c'])
    fig.update_layout(template='plotly_white', height=400)
    return fig


@app.callback(Output('price-segments', 'figure'), Input('price-segments', 'id'))
def update_price_segments(_):
    segment_counts = df['price_segment'].value_counts().reset_index()
    segment_counts.columns = ['segment', 'count']
    order = ['Эконом (до 1500)', 'Средний (1500-3000)', 'Комфорт (3000-5000)', 'Премиум (5000+)', 'Нет данных']
    segment_counts['order'] = segment_counts['segment'].apply(lambda x: order.index(x) if x in order else 999)
    segment_counts = segment_counts.sort_values('order')
    fig = px.bar(segment_counts, x='segment', y='count', 
                 title='Распределение по ценовым сегментам',
                 labels={'segment': 'Ценовой сегмент', 'count': 'Количество'},
                 color='segment', color_discrete_sequence=['#2ecc71', '#3498db', '#f39c12', '#e74c3c', '#95a5a6'])
    fig.update_layout(template='plotly_white', height=400, showlegend=False)
    return fig


@app.callback(Output('map', 'figure'), Input('map', 'id'))
def update_map(_):
    color_map = {
        'Отличный': '#27AE60',
        'Хороший': '#3B6FD4',
        'Средний': '#F5A623',
        'Низкий': '#E74C3C',
        'Нет рейтинга': '#AAB0C0'
    }
    fig = px.scatter_mapbox(map_data, lat='lat', lon='lon', color='rating_cat',
                            hover_name='name', hover_data={'price': True, 'rating': True, 'reviews': True},
                            color_discrete_map=color_map, zoom=8, center={'lat': 55.75, 'lon': 37.62},
                            title='Расположение пансионатов', mapbox_style='open-street-map')
    fig.update_layout(height=400, margin=dict(t=40, b=10, l=10, r=10))
    return fig


@app.callback(Output('top-rating', 'figure'), Input('top-rating', 'id'))
def update_top_rating(_):
    top_data = df[df['rating'] > 0].nlargest(10, 'rating')[['name', 'rating', 'reviews', 'source']]
    fig = px.bar(top_data[::-1], x='rating', y='name', orientation='h',
                 title='Топ-10 пансионатов по рейтингу',
                 labels={'rating': 'Рейтинг', 'name': 'Название'},
                 color='rating', color_continuous_scale='Viridis',
                 text='reviews', hover_data=['source'])
    fig.update_layout(template='plotly_white', height=450)
    fig.update_traces(texttemplate='%{text} отзывов', textposition='outside', textfont_size=10)
    return fig


@app.callback(Output('top-services', 'figure'), Input('top-services', 'id'))
def update_top_services(_):
    fig = px.bar(services_df.head(15), x='Количество', y='Услуга', orientation='h',
                 title='Топ-15 самых популярных услуг',
                 labels={'Количество': 'Количество упоминаний', 'Услуга': ''},
                 color='Количество', color_continuous_scale='Oranges')
    fig.update_layout(template='plotly_white', height=450)
    return fig

if __name__ == '__main__':
    print("\nОткройте в браузере: http://127.0.0.1:8050")
    app.run(debug=True, port=8050)