# Sales Dashboard

A real-time Shopify sales dashboard for monitoring promotional campaigns.

## Features

- Real-time order and sales tracking
- Customer segmentation analysis
- Geographic distribution mapping
- Top-performing SKU analysis
- Configurable campaign periods

## Setup

1. Clone this repository
2. Install dependencies: `pip install -r requirements.txt`
3. Configure your settings in `.streamlit/secrets.toml` (see `.streamlit/secrets.toml.example`)
4. Run: `streamlit run main.py`

## Configuration

All configuration is managed through `.streamlit/secrets.toml`. Copy the example file and update with your values.

## Deployment

This app is designed to be deployed on Streamlit Cloud. Configure secrets in the Streamlit Cloud dashboard.