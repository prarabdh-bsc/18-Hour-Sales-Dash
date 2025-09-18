import os
import streamlit as st
from datetime import datetime
import pytz
from typing import List, Dict, Any

class Config:
    def __init__(self):
        self._config = self._load_config()
        self._validate_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from Streamlit secrets with fallbacks"""
        try:
            return {
                # Shopify Configuration
                "ACCESS_TOKEN": st.secrets["shopify"]["access_token"],
                "SHOP_NAME": st.secrets["shopify"]["shop_name"],
                "API_VERSION": st.secrets["shopify"]["api_version"],
                
                # Campaign Configuration
                "TARGET_TAGS": st.secrets["campaign"]["target_tags"],
                "SALE_START_DATE": st.secrets["campaign"]["sale_start_date"],
                "SALE_START_TIME": st.secrets["campaign"]["sale_start_time"],
                "SALE_END_DATE": st.secrets["campaign"]["sale_end_date"],
                "SALE_END_TIME": st.secrets["campaign"]["sale_end_time"],
                "TIMEZONE": st.secrets["campaign"]["timezone"],
                
                # Dashboard Configuration
                "MAIN_REFRESH_INTERVAL": st.secrets["dashboard"]["main_refresh_interval"],
                "SKU_REFRESH_INTERVAL": st.secrets["dashboard"]["sku_refresh_interval"],
                "MAP_REFRESH_INTERVAL": st.secrets["dashboard"]["map_refresh_interval"],
                "CUSTOMER_REFRESH_INTERVAL": st.secrets["dashboard"]["customer_refresh_interval"],
                "STATE_REFRESH_INTERVAL": st.secrets["dashboard"]["state_refresh_interval"],
            }
        except Exception as e:
            st.error(f"Configuration Error: {str(e)}")
            st.error("Please ensure your .streamlit/secrets.toml file is properly configured.")
            st.stop()
    
    def _validate_config(self):
        """Validate required configuration values"""
        required_fields = ["ACCESS_TOKEN", "SHOP_NAME", "TARGET_TAGS"]
        
        for field in required_fields:
            if not self._config.get(field):
                st.error(f"Missing required configuration: {field}")
                st.stop()
        
        # Validate date formats
        try:
            datetime.strptime(self._config["SALE_START_DATE"], "%Y-%m-%d")
            datetime.strptime(self._config["SALE_END_DATE"], "%Y-%m-%d")
            datetime.strptime(self._config["SALE_START_TIME"], "%H:%M")
            datetime.strptime(self._config["SALE_END_TIME"], "%H:%M")
        except ValueError as e:
            st.error(f"Invalid date/time format in configuration: {str(e)}")
            st.stop()
    
    @property
    def ACCESS_TOKEN(self) -> str:
        return self._config["ACCESS_TOKEN"]
    
    @property
    def SHOP_NAME(self) -> str:
        return self._config["SHOP_NAME"]
    
    @property
    def API_VERSION(self) -> str:
        return self._config["API_VERSION"]
    
    @property
    def TARGET_TAGS(self) -> List[str]:
        return self._config["TARGET_TAGS"]
    
    @property
    def GRAPHQL_ENDPOINT(self) -> str:
        return f"https://{self.SHOP_NAME}.myshopify.com/admin/api/{self.API_VERSION}/graphql.json"
    
    @property
    def HEADERS(self) -> Dict[str, str]:
        return {
            "Content-Type": "application/json",
            "X-Shopify-Access-Token": self.ACCESS_TOKEN
        }
    
    def get_timeframe(self):
        """Get the configured timeframe for the sale"""
        tz = pytz.timezone(self._config["TIMEZONE"])
        
        start_date_str = f"{self._config['SALE_START_DATE']} {self._config['SALE_START_TIME']}"
        end_date_str = f"{self._config['SALE_END_DATE']} {self._config['SALE_END_TIME']}"
        
        start_dt = tz.localize(datetime.strptime(start_date_str, "%Y-%m-%d %H:%M"))
        end_dt = tz.localize(datetime.strptime(end_date_str, "%Y-%m-%d %H:%M"))
        
        return start_dt.astimezone(pytz.UTC).isoformat(), end_dt.astimezone(pytz.UTC).isoformat(), end_dt
    
    @property
    def REFRESH_INTERVALS(self) -> Dict[str, int]:
        return {
            "main": self._config["MAIN_REFRESH_INTERVAL"],
            "sku": self._config["SKU_REFRESH_INTERVAL"],
            "map": self._config["MAP_REFRESH_INTERVAL"],
            "customer": self._config["CUSTOMER_REFRESH_INTERVAL"],
            "state": self._config["STATE_REFRESH_INTERVAL"]
        }

# Global config instance
config = Config()